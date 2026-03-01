"""
Failure Predictor — 基于历史模式预测即将发生的故障。

四种预测：级联故障、过载、重复失败、性能退化。
只返回confidence >= 0.5的预测。
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """故障预测结果。"""

    prediction_type: str  # cascade | overload | recurring_failure | slowdown
    confidence: float  # 0.0-1.0
    affected_teams: list[str]
    message: str
    recommended_action: str
    time_horizon_seconds: int  # 预计多久后发生


class Predictor:
    """基于历史模式和当前状态预测故障。"""

    def __init__(self, workspace_dir: Path, processing_timeout: float = 1800.0) -> None:
        self.workspace_dir = workspace_dir
        self.events_dir = workspace_dir / "events"
        self.history_path = self.events_dir / ".watchdog" / "history.jsonl"
        self.processing_timeout = processing_timeout

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def predict_all(self) -> list[Prediction]:
        """运行所有预测检查，返回confidence>=0.5的结果。"""
        predictions: list[Prediction] = []
        predictions.extend(self._predict_cascade())
        predictions.extend(self._predict_overload())
        predictions.extend(self._predict_recurring_failure())
        predictions.extend(self._predict_slowdown())
        return [p for p in predictions if p.confidence >= 0.5]

    # ------------------------------------------------------------------
    # Cascade
    # ------------------------------------------------------------------

    def _predict_cascade(self) -> list[Prediction]:
        """级联故障预测：processing事件超过avg_time的80%时，预警下游。"""
        predictions: list[Prediction] = []
        processing_dir = self.events_dir / "processing"
        if not processing_dir.exists():
            return predictions

        now = time.time()
        for f in processing_dir.glob("*.md"):
            meta = self._read_metadata(f)
            if not meta:
                continue

            age = now - f.stat().st_mtime
            # 超过timeout的80%
            if age < self.processing_timeout * 0.8:
                continue

            callback = meta.get("callback", {})
            if not isinstance(callback, dict):
                continue
            downstream = callback.get("team", "")
            if not downstream:
                continue

            source = meta.get("source_team", "unknown")
            factor = age / self.processing_timeout
            confidence = min(0.5 + (factor - 0.8) * 1.0, 0.95)

            predictions.append(Prediction(
                prediction_type="cascade",
                confidence=confidence,
                affected_teams=[source, downstream],
                message=f"Event {meta.get('event_id', '?')[:8]} processing at {factor:.1f}x timeout. "
                        f"Downstream team={downstream} may not receive callback.",
                recommended_action=f"Monitor {source}; prepare fallback for {downstream}",
                time_horizon_seconds=int(max(0, self.processing_timeout - age)),
            ))

        return predictions

    # ------------------------------------------------------------------
    # Overload
    # ------------------------------------------------------------------

    def _predict_overload(self) -> list[Prediction]:
        """过载预测：pending增速 > 消费速度。"""
        records = self._load_recent_records(minutes=30)
        if len(records) < 3:
            return []

        pending_counts = [r.get("pending_count", 0) for r in records]
        resolved_counts = [r.get("resolved_count", 0) for r in records]

        # 计算速率（每分钟）
        minutes = 30
        pending_rate = (pending_counts[-1] - pending_counts[0]) / minutes if minutes else 0
        consume_rate = (resolved_counts[-1] - resolved_counts[0]) / minutes if minutes else 0

        if pending_rate <= 0 or pending_rate <= consume_rate:
            return []

        # 估算多久会积压到危险水平（比如50个pending）
        current_pending = pending_counts[-1]
        threshold = 50
        net_rate = pending_rate - consume_rate
        if net_rate <= 0:
            return []
        time_to_threshold = int((threshold - current_pending) / net_rate * 60) if current_pending < threshold else 0

        confidence = min(0.5 + net_rate * 10, 0.95)

        return [Prediction(
            prediction_type="overload",
            confidence=confidence,
            affected_teams=["*"],
            message=f"Pending growing at {pending_rate:.2f}/min, consume at {consume_rate:.2f}/min. "
                    f"Current: {current_pending}. Est. critical in {time_to_threshold}s.",
            recommended_action="Increase EventBus polling frequency or add consumers",
            time_horizon_seconds=max(time_to_threshold, 0),
        )]

    # ------------------------------------------------------------------
    # Recurring failure
    # ------------------------------------------------------------------

    def _predict_recurring_failure(self) -> list[Prediction]:
        """重复故障预测：同一团队+事件类型连续失败。"""
        records = self._load_recent_records(minutes=120)
        predictions: list[Prediction] = []

        # 收集 (team, event_type) → 连续失败次数
        failure_streaks: Counter[str] = Counter()

        for rec in records:
            for alert in rec.get("alerts", []):
                if alert.get("check_type") not in ("STALE_PROCESSING", "CHAIN_BROKEN"):
                    continue
                team = self._extract_team(alert.get("message", ""))
                etype = self._extract_event_type(alert.get("message", ""))
                key = f"{team}:{etype}"
                failure_streaks[key] += 1

        for key, count in failure_streaks.items():
            if count < 2:
                continue
            team, etype = key.split(":", 1)
            confidence = min(0.5 + count * 0.15, 0.95)
            predictions.append(Prediction(
                prediction_type="recurring_failure",
                confidence=confidence,
                affected_teams=[team] if team else ["unknown"],
                message=f"Team={team} event_type={etype} failed {count} times in 2h. "
                        f"Next attempt will likely fail too.",
                recommended_action="Skip auto-retry, escalate to user. Check root cause.",
                time_horizon_seconds=300,
            ))

        return predictions

    # ------------------------------------------------------------------
    # Slowdown
    # ------------------------------------------------------------------

    def _predict_slowdown(self) -> list[Prediction]:
        """性能退化预测：最近1h avg vs 24h avg。"""
        records_1h = self._load_recent_records(minutes=60)
        records_24h = self._load_recent_records(minutes=1440)

        if len(records_1h) < 3 or len(records_24h) < 10:
            return []

        def avg_processing_from_records(recs: list[dict]) -> float:
            """从alert messages中提取平均处理时间。"""
            times: list[float] = []
            for rec in recs:
                for alert in rec.get("alerts", []):
                    msg = alert.get("message", "")
                    m = re.search(r"(\d+)s", msg)
                    if m:
                        times.append(float(m.group(1)))
            return sum(times) / len(times) if times else 0

        avg_1h = avg_processing_from_records(records_1h)
        avg_24h = avg_processing_from_records(records_24h)

        if avg_24h <= 0 or avg_1h <= avg_24h * 1.5:
            return []

        ratio = avg_1h / avg_24h
        confidence = min(0.5 + (ratio - 1.5) * 0.3, 0.9)

        return [Prediction(
            prediction_type="slowdown",
            confidence=confidence,
            affected_teams=["*"],
            message=f"Processing time degraded: 1h avg={avg_1h:.0f}s vs 24h avg={avg_24h:.0f}s "
                    f"({ratio:.1f}x slower).",
            recommended_action="Check system resources, external API latency, or model availability",
            time_horizon_seconds=3600,
        )]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_recent_records(self, minutes: int) -> list[dict]:
        """加载最近N分钟的history记录。"""
        if not self.history_path.exists():
            return []
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        results: list[dict] = []
        try:
            for line in self.history_path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                    if ts >= cutoff:
                        results.append(data)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        except Exception as e:
            logger.error("Failed to load history: %s", e)
        return results

    def _read_metadata(self, path: Path) -> dict | None:
        """读取事件文件的YAML front-matter。"""
        try:
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                return None
            parts = text.split("---", 2)
            if len(parts) < 3:
                return None
            return yaml.safe_load(parts[1]) or {}
        except Exception:
            return None

    @staticmethod
    def _extract_team(msg: str) -> str:
        """从message中提取team名。"""
        for prefix in ("team=", "source_team="):
            if prefix in msg:
                start = msg.index(prefix) + len(prefix)
                end = msg.find(" ", start)
                end = end if end != -1 else msg.find(",", start)
                end = end if end != -1 else len(msg)
                return msg[start:end].strip()
        return ""

    @staticmethod
    def _extract_event_type(msg: str) -> str:
        """从message中提取event_type。"""
        if "(" in msg and ")" in msg:
            start = msg.index("(") + 1
            end = msg.index(")", start)
            return msg[start:end]
        return ""

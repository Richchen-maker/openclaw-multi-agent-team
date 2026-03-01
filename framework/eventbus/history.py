"""
History Tracker — 记录每次Watchdog运行的结果，供Profiler和Predictor使用。

JSONL格式存储在 events/.watchdog/history.jsonl，自动轮转。
"""

from __future__ import annotations

import json
import logging
import tempfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class HistoryRecord:
    """单次Watchdog运行记录。"""

    timestamp: str  # ISO8601
    status: str  # HEALTHY / WARNING / CRITICAL
    pending_count: int
    processing_count: int
    resolved_count: int
    failed_count: int
    alerts: list[dict]  # [{level, check_type, event_id, message}]
    recoveries: list[dict]  # [{event_id, action, success, details}]
    predictions: list[dict]  # [{prediction_type, confidence, ...}]
    team_scores: dict[str, int]  # team_name → health_score


class HistoryTracker:
    """Append-only JSONL history with automatic rotation."""

    MAX_RECORDS = 10000  # ~7天 @ 每2分钟1条

    def __init__(self, workspace_dir: Path) -> None:
        self.events_dir = workspace_dir / "events"
        self.watchdog_dir = self.events_dir / ".watchdog"
        self.history_path = self.watchdog_dir / "history.jsonl"
        self.watchdog_dir.mkdir(parents=True, exist_ok=True)

    def record(self, record: HistoryRecord) -> None:
        """追加一条记录到history.jsonl。"""
        with open(self.history_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(record), ensure_ascii=False) + "\n")
        self._rotate_if_needed()

    def query(self, hours: int = 24) -> list[HistoryRecord]:
        """查询最近N小时的记录。"""
        if not self.history_path.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        results: list[HistoryRecord] = []

        for line in self._read_lines():
            try:
                data = json.loads(line)
                ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                if ts >= cutoff:
                    results.append(HistoryRecord(**data))
            except Exception:
                continue
        return results

    def get_recovery_stats(self, hours: int = 24) -> dict:
        """获取修复统计：成功/失败次数、最常见的修复类型。"""
        records = self.query(hours)
        total = 0
        success = 0
        action_counts: dict[str, int] = {}

        for rec in records:
            for r in rec.recoveries:
                total += 1
                if r.get("success"):
                    success += 1
                action = r.get("action", "unknown")
                action_counts[action] = action_counts.get(action, 0) + 1

        most_common = max(action_counts, key=action_counts.get) if action_counts else ""
        return {
            "total": total,
            "success": success,
            "failed": total - success,
            "success_rate": success / total if total else 0.0,
            "most_common_action": most_common,
            "action_counts": action_counts,
        }

    def get_alert_trends(self, hours: int = 24) -> dict:
        """获取告警趋势：每小时告警数、类型分布。"""
        records = self.query(hours)
        hourly: dict[str, int] = {}
        type_counts: dict[str, int] = {}

        for rec in records:
            try:
                hour_key = rec.timestamp[:13]  # YYYY-MM-DDTHH
            except Exception:
                hour_key = "unknown"
            hourly[hour_key] = hourly.get(hour_key, 0) + len(rec.alerts)
            for a in rec.alerts:
                ct = a.get("check_type", "unknown")
                type_counts[ct] = type_counts.get(ct, 0) + 1

        return {
            "hourly_alerts": hourly,
            "type_distribution": type_counts,
            "total_alerts": sum(type_counts.values()),
        }

    def _read_lines(self) -> list[str]:
        """读取history文件所有行。"""
        if not self.history_path.exists():
            return []
        return self.history_path.read_text(encoding="utf-8").strip().splitlines()

    def _rotate_if_needed(self) -> None:
        """超过MAX_RECORDS时只保留最新的80%。"""
        lines = self._read_lines()
        if len(lines) <= self.MAX_RECORDS:
            return

        keep = int(self.MAX_RECORDS * 0.8)
        trimmed = lines[-keep:]
        # 原子写：先写临时文件再rename
        tmp = self.history_path.with_suffix(".tmp")
        tmp.write_text("\n".join(trimmed) + "\n", encoding="utf-8")
        tmp.replace(self.history_path)
        logger.info("History rotated: %d → %d records", len(lines), keep)

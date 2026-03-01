"""
EventBus Watchdog — 智能监控跨团队自动协作流程。

检测卡死的事件链，自动修复或通知用户。
可作为独立进程运行，也可集成到OpenClaw cron。

5种检查:
  1. STALE_PENDING   — pending/中超时未dispatch
  2. STALE_PROCESSING — processing/中sub-agent超时
  3. CHAIN_BROKEN    — 事件链断裂(resolved有callback但无后续)
  4. FORMAT_ERROR    — YAML解析失败或缺必须字段
  5. BUS_DOWN        — Event Bus进程/心跳丢失
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .event import Event

# V2 modules — graceful fallback if not yet available
try:
    from .analyzer import EventAnalyzer
    from .profiler import TeamProfiler
    from .predictor import Predictor
    from .history import HistoryTracker
    from .recovery import RecoveryEngine, RecoveryResult, Strategy
    _V2_AVAILABLE = True
except ImportError:
    _V2_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Alert:
    """单条告警。"""

    level: str  # "WARNING" | "CRITICAL"
    check_type: str  # STALE_PENDING | STALE_PROCESSING | CHAIN_BROKEN | FORMAT_ERROR | BUS_DOWN
    event_id: str  # 相关事件ID，无则为空字符串
    message: str
    auto_recoverable: bool
    recovery_action: str


@dataclass
class WatchdogReport:
    """一轮检查的完整报告。"""

    timestamp: datetime
    alerts: list[Alert]
    status: str  # HEALTHY | WARNING | CRITICAL
    events_summary: dict[str, int] = field(default_factory=dict)
    # V2 fields
    predictions: list[Any] = field(default_factory=list)
    team_scores: dict[str, Any] = field(default_factory=dict)
    recoveries: list[Any] = field(default_factory=list)
    system_score: int = 100


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_WATCHDOG_CONFIG: dict[str, Any] = {
    "pending_timeout": 300,
    "processing_timeout": 1800,
    "chain_check_window": 3600,
    "auto_recover": True,
    "max_auto_retries": 2,
    "notify_on_warning": False,
    "notify_on_critical": True,
    "heartbeat_file": "eventbus_heartbeat",
    "heartbeat_max_age": 300,
}

# ---------------------------------------------------------------------------
# Watchdog
# ---------------------------------------------------------------------------


class Watchdog:
    """EventBus智能监控。"""

    def __init__(self, workspace_dir: Path, config: dict[str, Any] | None = None) -> None:
        self.workspace_dir = Path(workspace_dir)
        self.events_dir = self.workspace_dir / "events"
        self.config = {**DEFAULT_WATCHDOG_CONFIG, **(config or {})}
        self.alerts: list[Alert] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def check_all(self) -> WatchdogReport:
        """运行所有检查，返回报告。V2增加分析+预测+评分。"""
        self.alerts = []
        self._check_stale_pending()
        self._check_stale_processing()
        self._check_chain_integrity()
        self._check_event_format()
        self._check_bus_health()

        summary = self._events_summary()
        predictions: list[Any] = []
        team_scores: dict[str, Any] = {}
        system_score = 100

        # V2: 深度分析 + 预测 + 评分
        if _V2_AVAILABLE:
            try:
                # Analyzer: 对每个告警做根因分析
                analyzer = EventAnalyzer(self.workspace_dir)
                for alert in self.alerts:
                    if alert.event_id:
                        event_path = self._find_event_file(alert.event_id)
                        if event_path:
                            analysis = analyzer.analyze(event_path)
                            alert.recovery_action = f"[V2] {analysis.root_cause.value}: {analysis.recommendation}"

                # Predictor: 预测性告警
                predictor = Predictor(self.workspace_dir)
                predictions = predictor.predict()
                for pred in predictions:
                    if pred.get("severity") == "CRITICAL":
                        self.alerts.append(Alert(
                            level="WARNING",
                            check_type="PREDICTION",
                            event_id="",
                            message=f"[Predicted] {pred.get('message', '')}",
                            auto_recoverable=False,
                            recovery_action=pred.get("recommendation", "Monitor closely"),
                        ))

                # Profiler: 团队健康评分
                profiler = TeamProfiler(self.workspace_dir)
                team_scores = profiler.score_all()
                scores = [v.get("score", 100) if isinstance(v, dict) else v for v in team_scores.values()]
                system_score = int(sum(scores) / len(scores)) if scores else 100
            except Exception as e:
                logger.warning("V2 modules error (falling back to V1): %s", e)

        status = "HEALTHY"
        if self.alerts:
            status = "CRITICAL" if any(a.level == "CRITICAL" for a in self.alerts) else "WARNING"

        report = WatchdogReport(
            timestamp=datetime.now(timezone.utc),
            alerts=list(self.alerts),
            status=status,
            events_summary=summary,
            predictions=predictions,
            team_scores=team_scores,
            system_score=system_score,
        )

        # V2: 记录历史
        if _V2_AVAILABLE:
            try:
                history = HistoryTracker(self.workspace_dir)
                history.record(report)
            except Exception as e:
                logger.warning("History recording failed: %s", e)

        return report

    def auto_recover(self, alert: Alert) -> bool:
        """尝试自动修复单条告警。返回是否成功。"""
        if not alert.auto_recoverable:
            logger.info("Alert %s not auto-recoverable, skipping", alert.check_type)
            return False

        if alert.check_type == "STALE_PENDING":
            return self._recover_stale_pending()
        elif alert.check_type == "STALE_PROCESSING":
            return self._recover_stale_processing(alert.event_id)
        elif alert.check_type == "CHAIN_BROKEN":
            return self._recover_chain_broken(alert.event_id)
        elif alert.check_type == "FORMAT_ERROR":
            return self._recover_format_error(alert.event_id)
        return False

    def auto_recover_all(self, report: WatchdogReport) -> list[tuple[Alert, bool]]:
        """对报告中所有可修复的告警执行自动修复。V2使用智能修复引擎。"""
        if not self.config.get("auto_recover", True):
            return []
        results: list[tuple[Alert, bool]] = []

        if _V2_AVAILABLE:
            engine = RecoveryEngine(self.workspace_dir, self.config)
            analyzer = EventAnalyzer(self.workspace_dir)
            for alert in report.alerts:
                if not alert.auto_recoverable:
                    continue
                try:
                    event_path = self._find_event_file(alert.event_id) if alert.event_id else None
                    if event_path:
                        analysis = analyzer.analyze(event_path)
                        strategy = engine.select_strategy(analysis)
                        result = engine.execute(strategy, event_path, analysis)
                        report.recoveries.append(result)
                        results.append((alert, result.success))
                        logger.info("V2 recover %s [%s] strategy=%s: %s",
                                    alert.check_type, alert.event_id[:8] if alert.event_id else "-",
                                    strategy.value, "OK" if result.success else "FAILED")
                    else:
                        # No file found, fall back to V1
                        ok = self.auto_recover(alert)
                        results.append((alert, ok))
                except Exception as e:
                    logger.warning("V2 recovery failed for %s, falling back to V1: %s", alert.event_id[:8] if alert.event_id else "-", e)
                    ok = self.auto_recover(alert)
                    results.append((alert, ok))
        else:
            for alert in report.alerts:
                if alert.auto_recoverable:
                    ok = self.auto_recover(alert)
                    results.append((alert, ok))
                    logger.info("Auto-recover %s [%s]: %s", alert.check_type, alert.event_id[:8] if alert.event_id else "-", "OK" if ok else "FAILED")
        return results

    def format_report(self, report: WatchdogReport) -> str:
        """格式化报告为人类可读文本。"""
        lines: list[str] = []
        icon = {"HEALTHY": "✅", "WARNING": "⚠️", "CRITICAL": "🔴"}.get(report.status, "❓")
        lines.append(f"{icon} EventBus Watchdog — {report.status}")
        lines.append(f"Time: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        s = report.events_summary
        if s:
            lines.append(f"Events: pending={s.get('pending', 0)} processing={s.get('processing', 0)} "
                         f"resolved={s.get('resolved', 0)} failed={s.get('failed', 0)}")

        if not report.alerts:
            lines.append("No issues detected.")
        else:
            lines.append(f"\n{len(report.alerts)} alert(s):")
            for a in report.alerts:
                fix = " [auto-recoverable]" if a.auto_recoverable else ""
                lines.append(f"  [{a.level}] {a.check_type}: {a.message}{fix}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------

    def _check_stale_pending(self) -> None:
        """检查pending/中超时未dispatch的事件。"""
        timeout = self.config["pending_timeout"]
        now = datetime.now(timezone.utc)
        for ev, _path in self._load_events("pending"):
            age = self._event_age(ev, now)
            if age is not None and age > timeout:
                target = ev.target_team or "(auto-route)"
                self.alerts.append(Alert(
                    level="WARNING" if age < timeout * 3 else "CRITICAL",
                    check_type="STALE_PENDING",
                    event_id=ev.event_id,
                    message=f"Event {ev.event_id[:8]} ({ev.event_type}) pending for {int(age)}s, target={target}",
                    auto_recoverable=True,
                    recovery_action="Run EventBus.run_once()",
                ))

    def _check_stale_processing(self) -> None:
        """检查processing/中超时的事件。"""
        timeout = self.config["processing_timeout"]
        now = datetime.now(timezone.utc)
        for ev, _path in self._load_events("processing"):
            age = self._event_age(ev, now)
            if age is not None and age > timeout:
                self.alerts.append(Alert(
                    level="CRITICAL",
                    check_type="STALE_PROCESSING",
                    event_id=ev.event_id,
                    message=f"Event {ev.event_id[:8]} ({ev.event_type}) stuck in processing for {int(age)}s, team={ev.source_team}",
                    auto_recoverable=True,
                    recovery_action="Move to failed/ and emit retry event",
                ))

    def _check_chain_integrity(self) -> None:
        """检查事件链完整性——最关键的检查。

        逻辑：遍历resolved/中有callback的事件，检查是否存在后续事件。
        如果resolved事件有callback且超过chain_check_window没有后续 → CHAIN_BROKEN。
        """
        window = self.config["chain_check_window"]
        now = datetime.now(timezone.utc)

        # 收集所有目录中的事件ID，用于关联
        all_event_ids: set[str] = set()
        all_events_by_dir: dict[str, list[tuple[Event, Path]]] = {}
        for d in ("pending", "processing", "resolved", "failed"):
            evts = self._load_events(d)
            all_events_by_dir[d] = evts
            for ev, _ in evts:
                all_event_ids.add(ev.event_id)

        # 构建 (source_team, event_type, chain_depth) → set of dirs 的索引
        # 用于检查后续事件是否存在
        all_events_index: dict[str, set[str]] = {}  # event_id → set of dirs
        for d, evts in all_events_by_dir.items():
            for ev, _ in evts:
                all_events_index.setdefault(ev.event_id, set()).add(d)

        # 检查resolved/中有callback的事件
        for ev, _ in all_events_by_dir.get("resolved", []):
            callback = ev.metadata.get("callback")
            if not callback or not isinstance(callback, dict):
                continue

            age = self._event_age(ev, now)
            if age is None or age > window:
                # 超出检查窗口，跳过
                continue

            # 检查是否有chain_depth + 1的后续事件
            next_depth = ev.chain_depth + 1
            has_successor = False
            for d in ("pending", "processing", "resolved"):
                for other_ev, _ in all_events_by_dir.get(d, []):
                    if other_ev.chain_depth == next_depth and other_ev.event_id != ev.event_id:
                        # 粗略关联：后续事件的source_team应为callback目标
                        cb_team = callback.get("team", "")
                        if other_ev.source_team == cb_team or other_ev.target_team == cb_team or not cb_team:
                            has_successor = True
                            break
                if has_successor:
                    break

            if not has_successor and age > self.config["pending_timeout"]:
                cb_team = callback.get("team", "unknown")
                self.alerts.append(Alert(
                    level="CRITICAL",
                    check_type="CHAIN_BROKEN",
                    event_id=ev.event_id,
                    message=f"Chain broken after {ev.event_id[:8]} ({ev.event_type}, depth={ev.chain_depth}). "
                            f"Callback to team={cb_team} not dispatched after {int(age)}s",
                    auto_recoverable=True,
                    recovery_action=f"Re-emit callback event to team={cb_team}",
                ))

    def _check_event_format(self) -> None:
        """检查所有目录中事件文件的YAML格式。"""
        required = {"event_id", "event_type", "source_team", "status"}
        for d in ("pending", "processing", "resolved", "failed"):
            dirpath = self.events_dir / d
            if not dirpath.exists():
                continue
            for f in dirpath.glob("*.md"):
                try:
                    text = f.read_text(encoding="utf-8")
                    if not text.startswith("---"):
                        raise ValueError("No YAML front-matter")
                    parts = text.split("---", 2)
                    if len(parts) < 3:
                        raise ValueError("Malformed front-matter")
                    meta = yaml.safe_load(parts[1])
                    if not isinstance(meta, dict):
                        raise ValueError("Front-matter is not a mapping")
                    missing = required - set(meta.keys())
                    if missing:
                        raise ValueError(f"Missing fields: {missing}")
                    cd = meta.get("chain_depth", 0)
                    if not isinstance(cd, int):
                        raise ValueError(f"chain_depth is not int: {cd!r}")
                except Exception as e:
                    self.alerts.append(Alert(
                        level="WARNING",
                        check_type="FORMAT_ERROR",
                        event_id=f.stem,
                        message=f"Format error in {d}/{f.name}: {e}",
                        auto_recoverable=True,
                        recovery_action="Move to failed/",
                    ))

    def _check_bus_health(self) -> None:
        """检查Event Bus是否在运行（心跳文件或进程检测）。"""
        # 方式1: 心跳文件
        hb_file = self.events_dir / self.config["heartbeat_file"]
        if hb_file.exists():
            age = time.time() - hb_file.stat().st_mtime
            if age > self.config["heartbeat_max_age"]:
                self.alerts.append(Alert(
                    level="CRITICAL",
                    check_type="BUS_DOWN",
                    event_id="",
                    message=f"Heartbeat stale: last update {int(age)}s ago",
                    auto_recoverable=False,
                    recovery_action="Restart EventBus process",
                ))
            return

        # 方式2: 进程检测
        try:
            result = subprocess.run(
                ["pgrep", "-f", "eventbus.*run"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                self.alerts.append(Alert(
                    level="WARNING",
                    check_type="BUS_DOWN",
                    event_id="",
                    message="No EventBus process detected and no heartbeat file found",
                    auto_recoverable=False,
                    recovery_action="Start EventBus: python -m eventbus run",
                ))
        except Exception:
            # pgrep不可用，仅检查心跳
            self.alerts.append(Alert(
                level="WARNING",
                check_type="BUS_DOWN",
                event_id="",
                message="Cannot detect EventBus status (no heartbeat, pgrep unavailable)",
                auto_recoverable=False,
                recovery_action="Start EventBus or enable heartbeat",
            ))

    # ------------------------------------------------------------------
    # Recovery
    # ------------------------------------------------------------------

    def _recover_stale_pending(self) -> bool:
        """运行一次EventBus.run_once()来处理积压的pending事件。"""
        try:
            from .bus import EventBus
            bus = EventBus(workspace_dir=self.workspace_dir)
            processed = bus.run_once()
            logger.info("Recovery run_once processed %d events", processed)
            return True
        except Exception as e:
            logger.error("Recovery run_once failed: %s", e)
            return False

    def _recover_stale_processing(self, event_id: str) -> bool:
        """将超时的processing事件移到failed/，并写retry事件。"""
        processing_dir = self.events_dir / "processing"
        failed_dir = self.events_dir / "failed"
        failed_dir.mkdir(parents=True, exist_ok=True)

        for f in processing_dir.glob("*.md"):
            try:
                ev = Event.from_file(f)
            except Exception:
                continue
            if ev.event_id != event_id:
                continue

            # 检查retry次数
            retry_count = ev.metadata.get("_watchdog_retries", 0)
            if retry_count >= self.config["max_auto_retries"]:
                logger.warning("Max retries reached for %s, moving to failed/ only", event_id[:8])
                ev.status = "failed"
                ev.to_file(failed_dir / ev.filename)
                f.unlink(missing_ok=True)
                return True

            # 移到failed/
            ev.status = "failed"
            ev.to_file(failed_dir / ev.filename)
            f.unlink(missing_ok=True)

            # 写retry事件到pending/
            retry_body = f"[Watchdog auto-retry #{retry_count + 1}]\n\n{ev.body}"
            retry_meta = {**ev.metadata}
            retry_meta["_watchdog_retries"] = retry_count + 1
            retry_ev = Event.emit(
                event_type=ev.event_type,
                severity=ev.severity,
                source_team=ev.source_team,
                source_role=ev.metadata.get("source_role", "watchdog"),
                body=retry_body,
                target_team=ev.target_team,
                target_mode=ev.target_mode,
                chain_depth=ev.chain_depth,
                callback=ev.metadata.get("callback"),
                events_dir=self.events_dir,
            )
            # 标记retry计数
            retry_ev.metadata["_watchdog_retries"] = retry_count + 1
            pending_path = self.events_dir / "pending" / retry_ev.filename
            retry_ev.to_file(pending_path)
            logger.info("Retry event emitted: %s → pending/", retry_ev.event_id[:8])
            return True

        logger.warning("Event %s not found in processing/", event_id[:8])
        return False

    def _recover_chain_broken(self, event_id: str) -> bool:
        """根据resolved事件的callback重新emit后续事件。"""
        resolved_dir = self.events_dir / "resolved"
        for f in resolved_dir.glob("*.md"):
            try:
                ev = Event.from_file(f)
            except Exception:
                continue
            if ev.event_id != event_id:
                continue

            callback = ev.metadata.get("callback")
            if not callback or not isinstance(callback, dict):
                return False

            cb_team = callback.get("team", "")
            cb_type = callback.get("event_type", ev.event_type)
            cb_body = callback.get("body", f"[Watchdog chain recovery from {ev.event_id[:8]}]")

            Event.emit(
                event_type=cb_type,
                severity=ev.severity,
                source_team=ev.source_team,
                source_role="watchdog",
                body=cb_body,
                target_team=cb_team,
                target_mode=callback.get("mode", "session"),
                chain_depth=ev.chain_depth + 1,
                events_dir=self.events_dir,
            )
            logger.info("Chain recovery: emitted %s → team=%s", cb_type, cb_team)
            return True

        return False

    def _recover_format_error(self, file_stem: str) -> bool:
        """将格式错误的文件移到failed/。"""
        failed_dir = self.events_dir / "failed"
        failed_dir.mkdir(parents=True, exist_ok=True)
        for d in ("pending", "processing", "resolved"):
            dirpath = self.events_dir / d
            for f in dirpath.glob("*.md"):
                if f.stem == file_stem:
                    dest = failed_dir / f.name
                    shutil.move(str(f), str(dest))
                    logger.info("Moved malformed %s/%s → failed/", d, f.name)
                    return True
        return False

    # ------------------------------------------------------------------
    # V2: Dashboard
    # ------------------------------------------------------------------

    def format_dashboard(self, report: WatchdogReport) -> str:
        """格式化健康仪表盘输出。"""
        lines: list[str] = []
        bar_full, bar_empty = "■", "□"

        def score_bar(score: int, width: int = 10) -> str:
            filled = max(0, min(width, round(score / 100 * width)))
            return bar_full * filled + bar_empty * (width - filled)

        lines.append("━━━━━ EventBus Health Dashboard ━━━━━")
        lines.append(f"System Score: {report.system_score}/100 {score_bar(report.system_score)}")
        lines.append("")

        # Team Health
        if report.team_scores:
            lines.append("Team Health:")
            for team, info in report.team_scores.items():
                if isinstance(info, dict):
                    score = info.get("score", 0)
                    avg_t = info.get("avg_duration", 0)
                    succ = info.get("success_rate", 0)
                else:
                    score, avg_t, succ = int(info), 0, 0
                lines.append(f"  {team:24s} {score:3d} {score_bar(score)}  avg {int(avg_t)}s   success {int(succ * 100) if succ <= 1 else int(succ)}%")
        else:
            lines.append("Team Health: (no data)")
        lines.append("")

        # Pipeline
        s = report.events_summary
        total = sum(s.values())
        lines.append("Pipeline (24h):")
        lines.append(f"  Total: {total} | Success: {s.get('resolved', 0)} | Failed: {s.get('failed', 0)} | Pending: {s.get('pending', 0)}")
        lines.append("")

        # Predictions
        lines.append("Predictions:")
        if report.predictions:
            for p in report.predictions:
                msg = p.get("message", str(p)) if isinstance(p, dict) else str(p)
                lines.append(f"  ⚠ {msg}")
        else:
            lines.append("  (none)")
        lines.append("")

        # Recoveries
        lines.append("Last 5 Recoveries:")
        recoveries = report.recoveries[-5:] if report.recoveries else []
        if recoveries:
            for r in recoveries:
                if hasattr(r, "strategy"):
                    ts = datetime.now(timezone.utc).strftime("%H:%M")
                    tag = "success" if r.success else "failed"
                    lines.append(f"  {ts} {r.strategy.value} {r.event_id[:8]} → {tag}")
                else:
                    lines.append(f"  {r}")
        else:
            lines.append("  (none)")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    def format_history(self, hours: int = 24) -> str:
        """格式化历史记录输出。"""
        if not _V2_AVAILABLE:
            return "History module not available."
        try:
            history = HistoryTracker(self.workspace_dir)
            records = history.query(hours=hours)
            if not records:
                return f"No watchdog history in the last {hours}h."
            lines = [f"Watchdog History (last {hours}h): {len(records)} runs"]
            for rec in records[-20:]:  # last 20
                ts = rec.get("timestamp", "?")
                status = rec.get("status", "?")
                alerts_n = rec.get("alert_count", 0)
                score = rec.get("system_score", "?")
                icon = {"HEALTHY": "✅", "WARNING": "⚠️", "CRITICAL": "🔴"}.get(status, "❓")
                lines.append(f"  {ts} {icon} {status} alerts={alerts_n} score={score}")
            return "\n".join(lines)
        except Exception as e:
            return f"History query failed: {e}"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_event_file(self, event_id: str) -> Path | None:
        """在所有目录中查找事件文件。"""
        if not event_id:
            return None
        for d in ("processing", "pending", "resolved", "failed"):
            dirpath = self.events_dir / d
            if not dirpath.exists():
                continue
            for f in dirpath.glob("*.md"):
                if event_id in f.stem:
                    return f
                # Also try parsing
                try:
                    ev = Event.from_file(f)
                    if ev.event_id == event_id:
                        return f
                except Exception:
                    pass
        return None

    def _load_events(self, directory: str) -> list[tuple[Event, Path]]:
        """加载指定目录中的所有事件，跳过解析失败的文件。"""
        dirpath = self.events_dir / directory
        if not dirpath.exists():
            return []
        results: list[tuple[Event, Path]] = []
        for f in sorted(dirpath.glob("*.md")):
            try:
                results.append((Event.from_file(f), f))
            except Exception:
                pass  # FORMAT_ERROR检查会单独处理
        return results

    def _event_age(self, ev: Event, now: datetime) -> float | None:
        """返回事件距今的秒数，解析失败返回None。"""
        try:
            ts = datetime.fromisoformat(ev.timestamp.replace("Z", "+00:00"))
            return (now - ts).total_seconds()
        except Exception:
            return None

    def _events_summary(self) -> dict[str, int]:
        """统计各目录事件数量。"""
        summary: dict[str, int] = {}
        for d in ("pending", "processing", "resolved", "failed"):
            p = self.events_dir / d
            summary[d] = len(list(p.glob("*.md"))) if p.exists() else 0
        return summary


# ---------------------------------------------------------------------------
# CLI entry: watchdog loop
# ---------------------------------------------------------------------------

def watchdog_loop(workspace_dir: Path, config: dict[str, Any] | None = None, interval: int = 120) -> None:
    """持续监控模式，每interval秒检查一次。"""
    wd = Watchdog(workspace_dir, config)
    logger.info("Watchdog loop started (interval=%ds)", interval)
    try:
        while True:
            report = wd.check_all()
            if report.status != "HEALTHY":
                print(wd.format_report(report))
                if wd.config.get("auto_recover", True):
                    wd.auto_recover_all(report)
            else:
                logger.debug("All healthy")
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Watchdog loop stopped")

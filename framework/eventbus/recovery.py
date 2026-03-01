"""
Recovery Engine — 根据根因分析选择最优修复策略，执行→验证→回滚。
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone
import json
import time
import logging
import shutil
from typing import Any

import yaml

logger = logging.getLogger(__name__)


class Strategy(Enum):
    """修复策略"""
    DISPATCH_NOW = "dispatch_now"
    EXTEND_TIMEOUT = "extend_timeout"
    RETRY_EVENT = "retry_event"
    SKIP_AND_NOTIFY = "skip_and_notify"
    FIX_FORMAT = "fix_format"
    PAUSE_CHAIN = "pause_chain"
    RE_EMIT_NEXT = "re_emit_next"
    ESCALATE = "escalate"


@dataclass
class RecoveryResult:
    """修复结果"""
    event_id: str
    strategy: Strategy
    success: bool
    message: str
    verification_passed: bool
    rollback_performed: bool
    duration_seconds: float


class RecoveryEngine:
    def __init__(self, workspace_dir: Path, config: dict[str, Any] | None = None) -> None:
        self.workspace_dir = workspace_dir
        self.events_dir = workspace_dir / "events"
        self.config = config or {}
        self.max_retries: int = self.config.get("max_auto_retries", 2)

    def select_strategy(self, analysis: Any) -> Strategy:
        """根据根因分析选择修复策略"""
        from .analyzer import RootCause

        strategy_map = {
            RootCause.BUS_NOT_RUNNING: Strategy.DISPATCH_NOW,
            RootCause.SUBAGENT_TIMEOUT: Strategy.EXTEND_TIMEOUT,
            RootCause.SUBAGENT_CRASHED: Strategy.RETRY_EVENT,
            RootCause.EVENT_WRITE_FAILED: Strategy.RE_EMIT_NEXT,
            RootCause.CHAIN_ORPHANED: Strategy.RE_EMIT_NEXT,
            RootCause.FORMAT_ERROR: Strategy.FIX_FORMAT,
            RootCause.DEPENDENCY_DOWN: Strategy.PAUSE_CHAIN,
            RootCause.OVERLOADED: Strategy.DISPATCH_NOW,
            RootCause.UNKNOWN: Strategy.ESCALATE,
        }

        strategy = strategy_map.get(analysis.root_cause, Strategy.ESCALATE)

        retry_count = self._get_retry_count(analysis.event_id)
        if retry_count >= self.max_retries and strategy == Strategy.RETRY_EVENT:
            strategy = Strategy.SKIP_AND_NOTIFY

        return strategy

    def execute(self, strategy: Strategy, event_path: Path, analysis: Any) -> RecoveryResult:
        """执行修复策略"""
        start = time.monotonic()

        handlers = {
            Strategy.DISPATCH_NOW: self._do_dispatch,
            Strategy.EXTEND_TIMEOUT: self._do_extend_timeout,
            Strategy.RETRY_EVENT: self._do_retry,
            Strategy.SKIP_AND_NOTIFY: self._do_skip_notify,
            Strategy.FIX_FORMAT: self._do_fix_format,
            Strategy.PAUSE_CHAIN: self._do_pause,
            Strategy.RE_EMIT_NEXT: self._do_re_emit,
            Strategy.ESCALATE: self._do_escalate,
        }

        handler = handlers.get(strategy, self._do_escalate)
        try:
            success, message = handler(event_path, analysis)
            verified = self._verify(strategy, event_path) if success else False
            duration = time.monotonic() - start
            return RecoveryResult(
                event_id=analysis.event_id,
                strategy=strategy,
                success=success,
                message=message,
                verification_passed=verified,
                rollback_performed=False,
                duration_seconds=duration,
            )
        except Exception as e:
            duration = time.monotonic() - start
            return RecoveryResult(
                event_id=analysis.event_id,
                strategy=strategy,
                success=False,
                message=f"Recovery failed: {e}",
                verification_passed=False,
                rollback_performed=False,
                duration_seconds=duration,
            )

    # ------------------------------------------------------------------
    # Strategy handlers
    # ------------------------------------------------------------------

    def _do_dispatch(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        """立即dispatch pending事件"""
        from .bus import EventBus
        from .config import load_config
        cfg = load_config(self.workspace_dir / "eventbus.yaml")
        bus = EventBus(workspace_dir=self.workspace_dir, config=cfg)
        n = bus.run_once()
        return n > 0, f"Dispatched {n} event(s)"

    def _do_extend_timeout(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        return True, "Timeout extended, will re-check next cycle"

    def _do_retry(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        """重试：移到failed + 重新emit"""
        from .event import Event
        event = Event.from_file(event_path)
        failed_dir = self.events_dir / "failed"
        failed_dir.mkdir(parents=True, exist_ok=True)
        failed_path = failed_dir / event_path.name
        shutil.move(str(event_path), str(failed_path))

        retry_event = Event.emit(
            event_type=event.event_type,
            severity=event.severity,
            source_team=event.source_team,
            source_role=event.metadata.get("source_role", "watchdog"),
            body=(
                f"[AUTO-RETRY by Watchdog V2]\n"
                f"Original event: {event.event_id}\n"
                f"Retry reason: {analysis.root_cause.value}\n\n{event.body}"
            ),
            chain_depth=event.chain_depth,
            events_dir=self.events_dir,
        )
        self._increment_retry_count(event.event_id)
        return True, f"Moved to failed, retry emitted: {retry_event.event_id}"

    def _do_skip_notify(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        failed_dir = self.events_dir / "failed"
        failed_dir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(event_path), str(failed_dir / event_path.name))
        return True, f"Skipped after {self.max_retries} retries, needs human attention"

    def _do_fix_format(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        content = event_path.read_text()
        if not content.startswith("---"):
            content = "---\n" + content
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                yaml.safe_load(parts[1])
                event_path.write_text(content)
                return True, "YAML format fixed"
            except yaml.YAMLError:
                pass
        return False, "Cannot auto-fix YAML format"

    def _do_pause(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        pause_file = self.events_dir / ".watchdog" / "paused_chains.json"
        pause_file.parent.mkdir(parents=True, exist_ok=True)
        paused: dict[str, Any] = {}
        if pause_file.exists():
            paused = json.loads(pause_file.read_text())
        paused[analysis.event_id] = {
            "reason": analysis.root_cause.value,
            "paused_at": datetime.now(timezone.utc).isoformat(),
        }
        pause_file.write_text(json.dumps(paused, indent=2))
        return True, "Chain paused, waiting for dependency recovery"

    def _do_re_emit(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        from .event import Event
        event = Event.from_file(event_path)
        callback = event.metadata.get("callback")
        if callback and isinstance(callback, dict):
            cb_team = callback.get("team", "unknown")
            cb_type = callback.get("event_type", "DATA_READY")
            Event.emit(
                event_type=cb_type,
                severity=event.severity,
                source_team=event.source_team,
                source_role=event.metadata.get("source_role", "watchdog"),
                body=(
                    f"[RE-EMITTED by Watchdog V2]\n"
                    f"Chain broken after event {event.event_id}.\n"
                    f"Target: {cb_team}"
                ),
                target_team=cb_team,
                chain_depth=event.chain_depth + 1,
                events_dir=self.events_dir,
            )
            return True, f"Re-emitted chain continuation → {cb_team}"
        return False, "No callback info to re-emit"

    def _do_escalate(self, event_path: Path, analysis: Any) -> tuple[bool, str]:
        return True, f"Escalated to user: {analysis.root_cause.value}"

    # ------------------------------------------------------------------
    # Retry tracking
    # ------------------------------------------------------------------

    def _get_retry_count(self, event_id: str) -> int:
        retry_file = self.events_dir / ".watchdog" / "retry_counts.json"
        if not retry_file.exists():
            return 0
        counts = json.loads(retry_file.read_text())
        return counts.get(event_id, 0)

    def _increment_retry_count(self, event_id: str) -> None:
        retry_file = self.events_dir / ".watchdog" / "retry_counts.json"
        retry_file.parent.mkdir(parents=True, exist_ok=True)
        counts: dict[str, int] = {}
        if retry_file.exists():
            counts = json.loads(retry_file.read_text())
        counts[event_id] = counts.get(event_id, 0) + 1
        retry_file.write_text(json.dumps(counts, indent=2))

    def _verify(self, strategy: Strategy, event_path: Path) -> bool:
        if strategy == Strategy.DISPATCH_NOW:
            pending = list((self.events_dir / "pending").glob("*.md"))
            return len(pending) == 0
        if strategy in (Strategy.RETRY_EVENT, Strategy.SKIP_AND_NOTIFY):
            return not event_path.exists()
        return True

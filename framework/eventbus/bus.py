"""
EventBus core: scan pending events, route, and dispatch.

Implements safety rules: chain depth limit, dedup, processing timeout.
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from .config import load_config, DEFAULT_CONFIG
from .event import Event
from .router import Router, DEFAULT_ROUTES
from .dispatcher import Dispatcher

logger = logging.getLogger(__name__)


SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "INFO": 4}


class EventBus:
    """Core event bus runtime."""

    def __init__(
        self,
        workspace_dir: Path | str,
        routes: dict[str, dict[str, str]] | None = None,
        config: dict[str, Any] | None = None,
        dispatcher: Dispatcher | None = None,
    ) -> None:
        self.workspace_dir = Path(workspace_dir)
        self.events_dir = self.workspace_dir / "events"
        self.router = Router(routes)
        self.config = config or load_config(self.workspace_dir / "eventbus.yaml")

        if dispatcher is not None:
            self.dispatcher = dispatcher
        elif self.config.get("dispatch_mode") == "live" or self._check_openclaw_available():
            from .dispatcher import OpenClawDispatcher
            self.dispatcher = OpenClawDispatcher(self.workspace_dir, self.config)
            logger.info("Using OpenClawDispatcher (live mode)")
        else:
            self.dispatcher = Dispatcher()
            logger.info("Using DefaultDispatcher (dry-run mode)")

        # 确保4个子目录存在
        for d in ["pending", "processing", "resolved", "failed"]:
            (self.events_dir / d).mkdir(parents=True, exist_ok=True)

        # 去重追踪: (source_team, event_type) → last_timestamp
        self._dedup_cache: dict[tuple[str, str], float] = {}

    @staticmethod
    def _check_openclaw_available() -> bool:
        """Check if the openclaw CLI is available in PATH."""
        import shutil
        return shutil.which("openclaw") is not None

    @staticmethod
    def _sort_by_priority(events: list[Event]) -> list[Event]:
        """按severity排序，CRITICAL最先处理"""
        return sorted(events, key=lambda e: SEVERITY_ORDER.get(e.severity, 99))

    def scan(self) -> list[Event]:
        """Scan pending/ directory for unprocessed events.

        Returns:
            List of Event objects sorted by timestamp.
        """
        pending_dir = self.events_dir / "pending"
        events: list[Event] = []
        for f in sorted(pending_dir.glob("*.md")):
            try:
                events.append(Event.from_file(f))
            except Exception as e:
                logger.error("Failed to parse %s: %s", f.name, e)
        logger.info("Scanned %d pending event(s)", len(events))
        return events

    def route(self, event: Event) -> dict[str, str] | None:
        """Resolve routing for an event.

        Returns:
            Route info dict or None.
        """
        # 事件自带target优先
        if event.target_team and event.target_mode:
            return {"target_team": event.target_team, "target_mode": event.target_mode}
        return self.router.resolve(event.event_type)

    def _check_dedup(self, event: Event) -> bool:
        """Check if event is a duplicate within the dedup window.

        Returns:
            True if duplicate (should skip).
        """
        key = (event.source_team, event.event_type)
        window = self.config.get("dedup_window", DEFAULT_CONFIG["dedup_window"])
        now = time.time()

        if key in self._dedup_cache:
            elapsed = now - self._dedup_cache[key]
            if elapsed < window:
                logger.warning("Dedup: skipping %s from %s (%.0fs ago)", event.event_type, event.source_team, elapsed)
                return True

        self._dedup_cache[key] = now
        return False

    def _check_chain_depth(self, event: Event) -> bool:
        """Check if chain depth exceeds limit.

        Returns:
            True if over limit (should reject).
        """
        max_depth = self.config.get("max_chain_depth", DEFAULT_CONFIG["max_chain_depth"])
        if event.chain_depth > max_depth:
            logger.error("Chain depth %d > max %d for event %s", event.chain_depth, max_depth, event.event_id[:8])
            return True
        return False

    def _move_event(self, event: Event, from_dir: str, to_dir: str) -> Path:
        """Move event file between status directories."""
        src = self.events_dir / from_dir / event.filename
        dst = self.events_dir / to_dir / event.filename
        event.status = to_dir
        if src.exists():
            src.rename(dst)
        else:
            # 文件名可能不完全匹配，重新写入
            event.to_file(dst)
        logger.debug("Moved %s: %s → %s", event.event_id[:8], from_dir, to_dir)
        return dst

    def _cleanup_processing_timeout(self) -> None:
        """Move timed-out processing events to failed/."""
        timeout_sec = self.config.get("processing_timeout", DEFAULT_CONFIG["processing_timeout"])
        now = datetime.now(timezone.utc)
        for f in (self.events_dir / "processing").glob("*.md"):
            try:
                ev = Event.from_file(f)
                ts = datetime.fromisoformat(ev.timestamp.replace("Z", "+00:00"))
                if (now - ts).total_seconds() > timeout_sec:
                    logger.warning("Processing timeout: %s (%.0fs)", ev.event_id[:8], (now - ts).total_seconds())
                    self._move_event(ev, "processing", "failed")
            except Exception as e:
                logger.error("Timeout check failed for %s: %s", f.name, e)

    def dispatch(self, event: Event, route_info: dict[str, str]) -> bool:
        """Dispatch an event to its target team.

        1. Move pending → processing
        2. Execute via dispatcher
        3. Move to resolved (success) or failed (error)

        Returns:
            True on success.
        """
        # 安全检查: chain depth
        if self._check_chain_depth(event):
            self._move_event(event, "pending", "failed")
            print(f"[WARN] Chain depth exceeded for {event.event_id[:8]}, moved to failed/", file=sys.stderr)
            return False

        # 安全检查: dedup
        if self._check_dedup(event):
            return False

        # pending → processing
        self._move_event(event, "pending", "processing")

        team = route_info["target_team"]
        mode = route_info["target_mode"]

        try:
            success = self.dispatcher.dispatch_team(team, mode, event)
            if success:
                self._move_event(event, "processing", "resolved")
            else:
                self._move_event(event, "processing", "failed")
            return success
        except Exception as e:
            logger.error("Dispatch failed for %s: %s", event.event_id[:8], e)
            self._move_event(event, "processing", "failed")
            return False

    def run_once(self) -> int:
        """Run one scan-route-dispatch cycle.

        Returns:
            Number of events processed.
        """
        # 先清理超时的processing事件
        self._cleanup_processing_timeout()

        events = self.scan()
        events = self._sort_by_priority(events)
        processed = 0
        for event in events:
            route_info = self.route(event)
            if route_info is None:
                logger.warning("No route for %s, skipping", event.event_type)
                continue
            self.dispatch(event, route_info)
            processed += 1
        return processed

    def run_loop(self, interval: int | None = None) -> None:
        """Continuously poll pending events.

        Args:
            interval: Poll interval in seconds. Uses config default if None.
        """
        interval = interval or self.config.get("poll_interval", DEFAULT_CONFIG["poll_interval"])
        logger.info("EventBus loop started (interval=%ds)", interval)
        try:
            while True:
                n = self.run_once()
                if n:
                    logger.info("Processed %d event(s)", n)
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("EventBus loop stopped")

    def status(self) -> dict[str, int]:
        """Return event counts per directory.

        Returns:
            Dict mapping directory name to file count.
        """
        result: dict[str, int] = {}
        for d in ["pending", "processing", "resolved", "failed"]:
            p = self.events_dir / d
            result[d] = len(list(p.glob("*.md"))) if p.exists() else 0
        return result

"""
Dispatcher: execute target team for a routed event.

Default implementation prints a shell command to stdout.
Subclass and override `execute()` for custom dispatch (e.g. openclaw sub-agent).
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

from .event import Event

logger = logging.getLogger(__name__)


class Dispatcher:
    """Abstract dispatcher. Default: print shell command to stdout."""

    def build_prompt(self, event: Event, route_info: dict[str, str]) -> str:
        """Build execution prompt from event data.

        Args:
            event: The event to dispatch.
            route_info: Dict with target_team and target_mode.

        Returns:
            Prompt string for the target team.
        """
        team = route_info["target_team"]
        mode = route_info["target_mode"]
        lines = [
            f"# Team Dispatch: {team} (Mode {mode})",
            f"",
            f"## Event",
            f"- **ID:** {event.event_id}",
            f"- **Type:** {event.event_type}",
            f"- **Severity:** {event.severity}",
            f"- **Source:** {event.source_team}/{event.metadata.get('source_role', 'unknown')}",
            f"- **Chain Depth:** {event.chain_depth}",
            f"",
            f"## Instructions",
            f"Execute team `{team}` in mode `{mode}`. Process the event below:",
            f"",
        ]
        if event.body:
            lines.append(event.body)
        return "\n".join(lines)

    def execute(self, team: str, mode: str, event: Event, prompt: str) -> bool:
        """Execute the dispatch. Override for custom behavior.

        Default: print shell command to stdout.

        Args:
            team: Target team name.
            mode: Execution mode.
            event: The event being dispatched.
            prompt: Generated prompt string.

        Returns:
            True if dispatch succeeded, False otherwise.
        """
        # 默认实现：输出命令到stdout，让上层编排决定如何执行
        cmd = (
            f'openclaw sessions spawn --runtime subagent '
            f'--label "{team}-{mode}-{event.event_id[:8]}" '
            f'--task "{prompt[:200]}..."'
        )
        print(f"[DISPATCH] {team} mode={mode} event={event.event_id[:8]}")
        print(cmd)
        logger.info("Dispatched %s → %s (mode %s)", event.event_id[:8], team, mode)
        return True

    def dispatch_team(self, team: str, mode: str, event: Event) -> bool:
        """High-level dispatch entry point.

        Args:
            team: Target team name.
            mode: Execution mode (A/B/C).
            event: Event to process.

        Returns:
            True on success.
        """
        prompt = self.build_prompt(event, {"target_team": team, "target_mode": mode})

        # severity=CRITICAL → stderr告警
        if event.severity == "CRITICAL":
            print(f"[CRITICAL] Event {event.event_id} type={event.event_type} "
                  f"from {event.source_team}", file=sys.stderr)

        return self.execute(team, mode, event, prompt)

"""
Dispatcher implementations for EventBus.

DefaultDispatcher: prints shell commands (dry-run / CI / non-OpenClaw environments)
OpenClawDispatcher: actually spawns OpenClaw sub-agents to process events
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

from .databus import DataBus
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

        if event.severity == "CRITICAL":
            print(f"[CRITICAL] Event {event.event_id} type={event.event_type} "
                  f"from {event.source_team}", file=sys.stderr)

        return self.execute(team, mode, event, prompt)


# Alias for backward compat
DefaultDispatcher = Dispatcher


class OpenClawDispatcher(Dispatcher):
    """Live dispatcher that spawns OpenClaw sub-agents via CLI.

    Uses ``openclaw sessions spawn`` to create a sub-agent for each event.
    The sub-agent receives a full task prompt with event context, team
    protocol, and instructions to write result events back to pending/.
    """

    def __init__(self, workspace_dir: Path | str, config: dict[str, Any] | None = None) -> None:
        self.workspace_dir = Path(workspace_dir)
        self.config = config or {}
        self.model: str | None = self.config.get("dispatch_model", None)

    def execute(self, team: str, mode: str, event: Event, prompt: str) -> bool:
        """Spawn an OpenClaw sub-agent to handle the event.

        Args:
            team: Target team name.
            mode: Execution mode.
            event: The event being dispatched.
            prompt: Generated prompt string (unused; we build our own).

        Returns:
            True if the spawn CLI call succeeded.
        """
        task_prompt = self._build_task_prompt(team, mode, event)
        label = f"eventbus-{team}-{mode}-{event.event_id[:8]}"

        cmd: list[str] = [
            "openclaw", "sessions", "spawn",
            "--runtime", "subagent",
            "--mode", "run",
            "--label", label,
            "--run-timeout", str(self.config.get("dispatch_timeout", 300)),
            "--task", task_prompt,
        ]

        if self.model:
            cmd.extend(["--model", self.model])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.workspace_dir),
            )
            if result.returncode == 0:
                logger.info("Dispatched %s → %s mode=%s (label=%s)", event.event_id[:8], team, mode, label)
                return True
            else:
                logger.error("Dispatch failed for %s: %s", event.event_id[:8], result.stderr.strip())
                return False
        except subprocess.TimeoutExpired:
            logger.error("Dispatch CLI timeout for %s", event.event_id[:8])
            return False
        except FileNotFoundError:
            logger.error("openclaw CLI not found in PATH")
            return False

    def _format_data_refs_section(self, event: Event) -> str:
        """Format data_refs into a prompt section, if any exist."""
        if not event.data_refs:
            return ""
        databus = DataBus(self.workspace_dir)
        refs = databus.parse_refs(event)
        if not refs:
            return ""
        return databus.format_refs_for_prompt(refs) + "\n\n"

    def _build_task_prompt(self, team: str, mode: str, event: Event) -> str:
        """Build a rich task prompt for the sub-agent.

        Includes team identity, event details, ORCHESTRATOR.md excerpt,
        and instructions to write result events back to pending/.
        """
        orchestrator_path = self.workspace_dir / team / "ORCHESTRATOR.md"
        orchestrator_content = ""
        if orchestrator_path.exists():
            try:
                orchestrator_content = orchestrator_path.read_text(encoding="utf-8")[:2000]
            except OSError:
                pass

        callback = getattr(event, "callback", None) or event.metadata.get("callback") or {}
        cb_team = callback.get("team", "unknown") if isinstance(callback, dict) else "unknown"
        cb_role = callback.get("resume_role", "CONDUCTOR") if isinstance(callback, dict) else "CONDUCTOR"
        source_role = event.metadata.get("source_role", "unknown")
        ws = self.workspace_dir

        return f"""# Event Bus Dispatch: {team} (Mode {mode})

## Your Identity
You are the CONDUCTOR of {team}, operating in Mode {mode}.
Workspace: {ws}

## Event to Process
- **Event ID:** {event.event_id}
- **Type:** {event.event_type}
- **Severity:** {event.severity}
- **Source:** {event.source_team}/{source_role}
- **Chain Depth:** {event.chain_depth}

## Event Context
{event.body or '(no body)'}

{self._format_data_refs_section(event)}
## Instructions
1. Read your team's ORCHESTRATOR.md at {team}/ORCHESTRATOR.md for role definitions and procedures
2. Execute the appropriate response for this event type
3. Write outputs to {team}/output/ directory
4. **CRITICAL: When done, you MUST write a result event** to events/pending/:

If you completed the task successfully:
```bash
cat > {ws}/events/pending/$(date +%Y%m%d_%H%M%S)_DATA_READY_$(uuidgen | cut -c1-8).md << 'EOF'
---
event_id: "evt-$(uuidgen | cut -c1-8)"
event_type: DATA_READY
severity: LOW
source_team: {team}
source_role: CONDUCTOR
timestamp: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
status: pending
chain_depth: {event.chain_depth + 1}
callback:
  team: {cb_team}
  resume_role: {cb_role}
---
[Describe what you accomplished and where the output data is]
EOF
```

If you encountered a blocker:
Write the appropriate event type (CRAWL_BLOCKED, DATA_GAP, etc.) with chain_depth={event.chain_depth + 1}

5. After writing the event file, your task is complete.

## Team Protocol (excerpt)
{orchestrator_content[:1500] if orchestrator_content else '(No ORCHESTRATOR.md found for this team)'}
"""

"""
Dispatcher implementations for EventBus.

DefaultDispatcher: prints shell commands (dry-run / CI / non-OpenClaw environments)
OpenClawDispatcher: writes dispatch request files for Watchdog cron to process
"""

from __future__ import annotations

import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .databus import DataBus
from .event import Event

logger = logging.getLogger(__name__)


@dataclass
class DispatchRequest:
    """A dispatch request written to events/.dispatch/ for Watchdog cron pickup."""
    team: str
    mode: str
    event_id: str
    prompt: str
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_file(self, dispatch_dir: Path) -> Path:
        """Write request as YAML to dispatch_dir."""
        dispatch_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "team": self.team,
            "mode": self.mode,
            "event_id": self.event_id,
            "prompt": self.prompt,
            "status": self.status,
            "created_at": self.created_at,
        }
        filename = f"{self.created_at.replace(':', '').replace('-', '')[:15]}_{self.team}_{self.request_id}.yaml"
        path = dispatch_dir / filename
        path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        return path


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


class CronDispatcher(Dispatcher):
    """Cron-based dispatcher: writes YAML request files for Watchdog cron pickup.

    This is the default dispatch engine. Watchdog cron polls events/.dispatch/
    and spawns sub-agents for each pending request.
    """

    def __init__(self, workspace_dir: Path | str, config: dict[str, Any] | None = None) -> None:
        self.workspace_dir = Path(workspace_dir)
        self.config = config or {}

    def execute(self, team: str, mode: str, event: Event, prompt: str) -> bool:
        """Write dispatch request YAML to events/.dispatch/."""
        dispatch_dir = self.workspace_dir / "events" / ".dispatch"
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        request = DispatchRequest(
            team=team,
            mode=mode,
            event_id=event.event_id,
            prompt=prompt,
        )
        try:
            filename = f"{ts}_{team}_{event.event_id[:8]}.yaml"
            dispatch_dir.mkdir(parents=True, exist_ok=True)
            data = {
                "team": request.team,
                "mode": request.mode,
                "event_id": request.event_id,
                "prompt": request.prompt,
                "status": request.status,
                "created_at": request.created_at,
            }
            path = dispatch_dir / filename
            path.write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True), encoding="utf-8")
            logger.info("CronDispatcher: wrote %s", path.name)
            return True
        except Exception as e:
            logger.error("CronDispatcher failed for %s: %s", event.event_id[:8], e)
            return False

    @staticmethod
    def poll_requests(workspace_dir: Path | str) -> list[Path]:
        """Scan events/.dispatch/ for pending YAML request files."""
        dispatch_dir = Path(workspace_dir) / "events" / ".dispatch"
        if not dispatch_dir.exists():
            return []
        return sorted(dispatch_dir.glob("*.yaml"))

    @staticmethod
    def mark_dispatched(request_file: Path) -> None:
        """Mark a request as dispatched by moving it to .dispatch/done/."""
        done_dir = request_file.parent / "done"
        done_dir.mkdir(parents=True, exist_ok=True)
        dest = done_dir / request_file.name
        request_file.rename(dest)
        logger.info("Marked dispatched: %s → done/", request_file.name)


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
        """Write a dispatch request file for Watchdog cron to pick up.

        Args:
            team: Target team name.
            mode: Execution mode.
            event: The event being dispatched.
            prompt: Generated prompt string (unused; we build our own).

        Returns:
            True if the request file was written successfully.
        """
        task_prompt = self._build_task_prompt(team, mode, event)
        dispatch_dir = self.workspace_dir / "events" / ".dispatch"

        request = DispatchRequest(
            team=team,
            mode=mode,
            event_id=event.event_id,
            prompt=task_prompt,
        )

        try:
            path = request.to_file(dispatch_dir)
            logger.info("Dispatch request written: %s → %s (mode=%s)", event.event_id[:8], team, path.name)
            return True
        except Exception as e:
            logger.error("Failed to write dispatch request for %s: %s", event.event_id[:8], e)
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

"""
Standardized event write-back templates.

Provides shell script and Python functions for sub-agents to write events
back to events/pending/.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml


def generate_event_script(
    event_type: str,
    source_team: str,
    source_role: str,
    severity: str,
    chain_depth: int,
    body: str,
    workspace_dir: Path,
) -> str:
    """Generate a shell script string that writes a standardized event file.

    Args:
        event_type: Event type (e.g. DATA_READY).
        source_team: Originating team.
        source_role: Role within team.
        severity: LOW/MEDIUM/HIGH/CRITICAL.
        chain_depth: Current chain depth.
        body: Event body content.
        workspace_dir: Root workspace directory.

    Returns:
        Shell script string.
    """
    pending_dir = Path(workspace_dir) / "events" / "pending"
    short_id = str(uuid.uuid4())[:8]
    # Escape single quotes in body for shell safety
    safe_body = body.replace("'", "'\\''")

    return f"""#!/bin/bash
PENDING_DIR='{pending_dir}'
mkdir -p "$PENDING_DIR"
FILENAME="$(date +%Y%m%d_%H%M%S)_{event_type}_{short_id}.md"

cat > "$PENDING_DIR/$FILENAME" << 'EVENTEOF'
---
event_id: '{short_id}-{str(uuid.uuid4())[:8]}'
event_type: '{event_type}'
severity: '{severity}'
source_team: '{source_team}'
source_role: '{source_role}'
timestamp: '$(date -u +%Y-%m-%dT%H:%M:%SZ)'
status: 'pending'
chain_depth: {chain_depth}
---
{safe_body}
EVENTEOF
echo "Event written: $PENDING_DIR/$FILENAME"
"""


def write_event(
    event_type: str,
    source_team: str,
    source_role: str,
    severity: str,
    chain_depth: int,
    body: str,
    workspace_dir: Path,
) -> Path:
    """Write a standardized event file to events/pending/ (Python version).

    Args:
        event_type: Event type.
        source_team: Originating team.
        source_role: Role within team.
        severity: LOW/MEDIUM/HIGH/CRITICAL.
        chain_depth: Current chain depth.
        body: Event body content.
        workspace_dir: Root workspace directory.

    Returns:
        Path to the written event file.
    """
    pending_dir = Path(workspace_dir) / "events" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    short_id = str(uuid.uuid4())[:8]
    event_id = f"evt-{short_id}"
    ts = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_file = now.strftime("%Y%m%d_%H%M%S")
    filename = f"{ts_file}_{event_type}_{short_id}.md"

    metadata = {
        "event_id": event_id,
        "event_type": event_type,
        "severity": severity,
        "source_team": source_team,
        "source_role": source_role,
        "timestamp": ts,
        "status": "pending",
        "chain_depth": chain_depth,
    }

    front = yaml.dump(metadata, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{front}---\n{body}\n"

    path = pending_dir / filename
    path.write_text(content, encoding="utf-8")
    return path

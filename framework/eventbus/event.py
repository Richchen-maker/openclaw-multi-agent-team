"""
Event data model.

Events are Markdown files with YAML front-matter (delimited by ---).
Provides serialization/deserialization and factory methods.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# 必须字段
REQUIRED_FIELDS = {"event_id", "event_type", "severity", "source_team", "source_role", "timestamp", "status"}


class Event:
    """Represents a single event with YAML metadata and Markdown body."""

    def __init__(self, metadata: dict[str, Any], body: str = "") -> None:
        self.metadata = metadata
        self.body = body

    # -- 属性快捷访问 --

    @property
    def event_id(self) -> str:
        return self.metadata["event_id"]

    @property
    def event_type(self) -> str:
        return self.metadata["event_type"]

    @property
    def severity(self) -> str:
        return self.metadata.get("severity", "INFO")

    @property
    def status(self) -> str:
        return self.metadata.get("status", "pending")

    @status.setter
    def status(self, value: str) -> None:
        self.metadata["status"] = value

    @property
    def source_team(self) -> str:
        return self.metadata.get("source_team", "")

    @property
    def chain_depth(self) -> int:
        return int(self.metadata.get("chain_depth", 0))

    @chain_depth.setter
    def chain_depth(self, value: int) -> None:
        self.metadata["chain_depth"] = value

    @property
    def timestamp(self) -> str:
        return self.metadata.get("timestamp", "")

    @property
    def target_team(self) -> str | None:
        return self.metadata.get("target_team")

    @property
    def target_mode(self) -> str | None:
        return self.metadata.get("target_mode")

    # -- 序列化 --

    @classmethod
    def from_file(cls, path: Path) -> Event:
        """Parse an event file (YAML front-matter + Markdown body).

        Args:
            path: Path to the .md event file.

        Returns:
            Event instance.
        """
        text = path.read_text(encoding="utf-8")
        # 分离front-matter和正文
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                metadata = yaml.safe_load(parts[1]) or {}
                body = parts[2].lstrip("\n")
            else:
                raise ValueError(f"Malformed front-matter in {path}")
        else:
            raise ValueError(f"No YAML front-matter found in {path}")

        # 校验必须字段
        missing = REQUIRED_FIELDS - set(metadata.keys())
        if missing:
            raise ValueError(f"Missing required fields in {path}: {missing}")

        return cls(metadata=metadata, body=body)

    def to_file(self, path: Path) -> None:
        """Write event to a Markdown file with YAML front-matter.

        Args:
            path: Destination file path.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        front = yaml.dump(self.metadata, default_flow_style=False, allow_unicode=True, sort_keys=False)
        content = f"---\n{front}---\n{self.body}"
        path.write_text(content, encoding="utf-8")
        logger.debug("Wrote event %s to %s", self.event_id, path)

    @property
    def filename(self) -> str:
        """Generate canonical filename: {timestamp}_{event_type}_{short_id}.md"""
        ts = self.timestamp.replace(":", "").replace("-", "").replace("T", "_")[:15]
        short_id = self.event_id[:8]
        return f"{ts}_{self.event_type}_{short_id}.md"

    # -- 工厂方法 --

    @classmethod
    def emit(
        cls,
        event_type: str,
        severity: str,
        source_team: str,
        source_role: str,
        body: str = "",
        *,
        target_team: str | None = None,
        target_mode: str | None = None,
        chain_depth: int = 0,
        callback: dict[str, Any] | None = None,
        events_dir: Path | None = None,
    ) -> Event:
        """Create a new event and optionally write it to pending/.

        Args:
            event_type: Type string (e.g. DATA_GAP).
            severity: INFO / WARNING / CRITICAL.
            source_team: Originating team name.
            source_role: Role within the team.
            body: Markdown body content.
            target_team: Override route target.
            target_mode: Override route mode.
            chain_depth: Current chain depth.
            callback: Optional callback info dict.
            events_dir: If provided, write to events_dir/pending/.

        Returns:
            The created Event.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        metadata: dict[str, Any] = {
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "severity": severity,
            "source_team": source_team,
            "source_role": source_role,
            "timestamp": now,
            "status": "pending",
            "chain_depth": chain_depth,
        }
        if target_team:
            metadata["target_team"] = target_team
        if target_mode:
            metadata["target_mode"] = target_mode
        if callback:
            metadata["callback"] = callback

        event = cls(metadata=metadata, body=body)

        # 如果指定了events_dir，自动写入pending/
        if events_dir is not None:
            pending_dir = events_dir / "pending"
            pending_dir.mkdir(parents=True, exist_ok=True)
            event.to_file(pending_dir / event.filename)
            logger.info("Emitted event %s → pending/", event.event_id)

        return event

    def __repr__(self) -> str:
        return f"<Event {self.event_type} [{self.severity}] {self.event_id[:8]}>"

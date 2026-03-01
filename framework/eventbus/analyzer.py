"""
Root Cause Analyzer — 分析事件卡死的真正原因。

不只是"超时了"，而是WHY：Bus没跑？sub-agent挂了？链路断裂？
基于文件系统状态和事件元数据做推断。
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timezone

import yaml

logger = logging.getLogger(__name__)


class RootCause(Enum):
    """故障根因分类。"""

    SUBAGENT_TIMEOUT = "subagent_timeout"
    SUBAGENT_CRASHED = "subagent_crashed"
    EVENT_WRITE_FAILED = "event_write_failed"
    DEPENDENCY_DOWN = "dependency_down"
    FORMAT_ERROR = "format_error"
    BUS_NOT_RUNNING = "bus_not_running"
    CHAIN_ORPHANED = "chain_orphaned"
    OVERLOADED = "overloaded"
    UNKNOWN = "unknown"


@dataclass
class Analysis:
    """根因分析结果。"""

    event_id: str
    root_cause: RootCause
    confidence: float  # 0.0-1.0
    evidence: list[str]
    suggested_strategy: str
    details: dict


class Analyzer:
    """分析pending/processing超时和链路断裂的根因。"""

    # processing超时的判定倍率
    TIMEOUT_SLOW_FACTOR = 1.5
    TIMEOUT_CRASH_FACTOR = 3.0

    def __init__(self, workspace_dir: Path, processing_timeout: float = 1800.0) -> None:
        self.workspace_dir = workspace_dir
        self.events_dir = workspace_dir / "events"
        self.processing_timeout = processing_timeout

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def analyze_stale_pending(self, event_path: Path, age_seconds: float) -> Analysis:
        """分析pending超时的根因。"""
        event_id = self._extract_event_id(event_path)
        evidence: list[str] = []

        # 1. 检查事件格式
        fmt_ok = self._check_format(event_path)
        if not fmt_ok:
            evidence.append(f"Event file has format errors: {event_path.name}")
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.FORMAT_ERROR,
                confidence=0.95,
                evidence=evidence,
                suggested_strategy="Fix event format or move to failed/",
                details={"path": str(event_path)},
            )

        # 2. 检查Bus是否在运行
        bus_running = self._is_bus_running()
        pending_count = self._count_files("pending")
        evidence.append(f"Bus heartbeat present: {bus_running}")
        evidence.append(f"Pending count: {pending_count}")
        evidence.append(f"Age: {age_seconds:.0f}s")

        # 3. 判定
        if not bus_running and pending_count <= 2:
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.BUS_NOT_RUNNING,
                confidence=0.9,
                evidence=evidence,
                suggested_strategy="Start EventBus: python -m eventbus run",
                details={"pending_count": pending_count},
            )

        if pending_count >= 5:
            evidence.append(f"High pending backlog ({pending_count} events)")
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.OVERLOADED,
                confidence=min(0.6 + pending_count * 0.05, 0.95),
                evidence=evidence,
                suggested_strategy="Scale consumers or increase polling frequency",
                details={"pending_count": pending_count},
            )

        # 默认：Bus在跑但就是没处理到（可能路由问题）
        return Analysis(
            event_id=event_id,
            root_cause=RootCause.UNKNOWN,
            confidence=0.4,
            evidence=evidence,
            suggested_strategy="Check EventBus routing config and logs",
            details={"pending_count": pending_count, "bus_running": bus_running},
        )

    def analyze_stale_processing(self, event_path: Path, age_seconds: float) -> Analysis:
        """分析processing超时的根因。"""
        event_id = self._extract_event_id(event_path)
        evidence: list[str] = [f"Processing age: {age_seconds:.0f}s"]
        meta = self._read_metadata(event_path)
        source_team = meta.get("source_team", "unknown") if meta else "unknown"
        evidence.append(f"Source team: {source_team}")

        # 检查resolved/中是否有同chain更高depth的事件（说明sub-agent完成了但processing没清理）
        if meta:
            chain_depth = int(meta.get("chain_depth", 0))
            has_successor = self._has_successor_event(chain_depth, meta.get("callback", {}))
            if has_successor:
                evidence.append("Found successor event in resolved/ — processing file was not cleaned up")
                return Analysis(
                    event_id=event_id,
                    root_cause=RootCause.EVENT_WRITE_FAILED,
                    confidence=0.85,
                    evidence=evidence,
                    suggested_strategy="Clean stale processing file, chain already continued",
                    details={"chain_depth": chain_depth, "source_team": source_team},
                )

        # 根据超时倍率判断
        slow_threshold = self.processing_timeout * self.TIMEOUT_SLOW_FACTOR
        crash_threshold = self.processing_timeout * self.TIMEOUT_CRASH_FACTOR

        if age_seconds < slow_threshold:
            evidence.append(f"Age < {slow_threshold:.0f}s (1.5x timeout) — likely still running but slow")
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.SUBAGENT_TIMEOUT,
                confidence=0.6,
                evidence=evidence,
                suggested_strategy="Wait longer or check sub-agent logs",
                details={"source_team": source_team, "factor": age_seconds / self.processing_timeout},
            )

        evidence.append(f"Age > {crash_threshold:.0f}s (3x timeout) — sub-agent likely crashed")
        confidence = 0.85 if age_seconds > crash_threshold else 0.7
        return Analysis(
            event_id=event_id,
            root_cause=RootCause.SUBAGENT_CRASHED,
            confidence=confidence,
            evidence=evidence,
            suggested_strategy="Move to failed/ and emit retry event",
            details={"source_team": source_team, "factor": age_seconds / self.processing_timeout},
        )

    def analyze_chain_break(self, last_resolved_event: Path) -> Analysis:
        """分析链路断裂的根因。"""
        event_id = self._extract_event_id(last_resolved_event)
        meta = self._read_metadata(last_resolved_event)
        evidence: list[str] = []

        if not meta:
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.FORMAT_ERROR,
                confidence=0.9,
                evidence=["Cannot read event metadata"],
                suggested_strategy="Check event file format",
                details={},
            )

        callback = meta.get("callback", {})
        if not callback or not isinstance(callback, dict):
            evidence.append("No callback defined — chain ends here naturally")
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.CHAIN_ORPHANED,
                confidence=0.5,
                evidence=evidence,
                suggested_strategy="Verify if chain should have continued",
                details={"has_callback": False},
            )

        cb_team = callback.get("team", "")
        evidence.append(f"Callback target team: {cb_team}")
        chain_depth = int(meta.get("chain_depth", 0))

        # 检查failed/中是否有对应事件（之前尝试过但失败了）
        failed_match = self._find_events_in_dir(
            "failed", target_team=cb_team, min_depth=chain_depth + 1
        )
        if failed_match:
            evidence.append(f"Found {len(failed_match)} failed event(s) for team={cb_team} at depth>={chain_depth + 1}")
            return Analysis(
                event_id=event_id,
                root_cause=RootCause.SUBAGENT_CRASHED,
                confidence=0.8,
                evidence=evidence,
                suggested_strategy="Check failed events and retry or escalate",
                details={"callback_team": cb_team, "failed_count": len(failed_match)},
            )

        # 完全没有后续事件
        evidence.append("No successor event found in any directory")
        return Analysis(
            event_id=event_id,
            root_cause=RootCause.EVENT_WRITE_FAILED,
            confidence=0.75,
            evidence=evidence,
            suggested_strategy=f"Re-emit callback event to team={cb_team}",
            details={"callback_team": cb_team, "chain_depth": chain_depth},
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _extract_event_id(self, path: Path) -> str:
        """从文件提取event_id，失败则用文件名。"""
        meta = self._read_metadata(path)
        if meta and "event_id" in meta:
            return meta["event_id"]
        return path.stem

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
        except Exception as e:
            logger.debug("Failed to read metadata from %s: %s", path, e)
            return None

    def _check_format(self, path: Path) -> bool:
        """检查事件文件格式是否正确。"""
        meta = self._read_metadata(path)
        if meta is None:
            return False
        required = {"event_id", "event_type", "source_team", "status"}
        return required.issubset(meta.keys())

    def _is_bus_running(self) -> bool:
        """检查EventBus心跳文件是否新鲜（<5分钟）。"""
        hb = self.events_dir / "eventbus_heartbeat"
        if not hb.exists():
            return False
        return (time.time() - hb.stat().st_mtime) < 300

    def _count_files(self, directory: str) -> int:
        """统计指定目录下的.md文件数。"""
        d = self.events_dir / directory
        if not d.exists():
            return 0
        return len(list(d.glob("*.md")))

    def _has_successor_event(self, chain_depth: int, callback: dict) -> bool:
        """检查resolved/中是否有chain_depth+1的后续事件。"""
        cb_team = callback.get("team", "") if isinstance(callback, dict) else ""
        for d in ("pending", "processing", "resolved"):
            for match in self._find_events_in_dir(d, target_team=cb_team, min_depth=chain_depth + 1):
                return True
        return False

    def _find_events_in_dir(
        self, directory: str, target_team: str = "", min_depth: int = 0
    ) -> list[Path]:
        """在指定目录中查找匹配条件的事件。"""
        d = self.events_dir / directory
        if not d.exists():
            return []
        results: list[Path] = []
        for f in d.glob("*.md"):
            meta = self._read_metadata(f)
            if not meta:
                continue
            depth = int(meta.get("chain_depth", 0))
            if depth < min_depth:
                continue
            if target_team:
                src = meta.get("source_team", "")
                tgt = meta.get("target_team", "")
                if target_team not in (src, tgt):
                    continue
            results.append(f)
        return results

"""
Team Evolver — 团队自进化引擎。

任务完成后自动提取可复用的方法论，下次同类事件直接跳过中间环节。
进化三阶段：
1. Extract（提取）：从resolved事件和产出中提取关键决策和方法
2. Crystallize（结晶）：写入知识库，标记为可复用模式
3. Shortcut（捷径）：下次同类事件，Router直接查知识库决定是否跳步
"""
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime, timezone
import json
import logging
import re

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """可复用的模式"""
    pattern_id: str
    event_type: str          # 触发事件类型
    context_keywords: list[str]  # 上下文关键词（用于匹配）
    source_team: str         # 产出团队
    solution_summary: str    # 方案摘要
    solution_path: str       # 完整方案路径
    success_count: int = 0   # 成功使用次数
    fail_count: int = 0      # 失败次数
    confidence: float = 0.0  # 置信度 0-1
    created_at: str = ""
    last_used_at: str = ""
    chain_shortcut: dict = field(default_factory=dict)


class Evolver:
    PATTERNS_FILE = ".watchdog/patterns.json"
    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.patterns_path = workspace_dir / "events" / self.PATTERNS_FILE
        self.patterns: list[Pattern] = []
        self._load()

    def extract_from_chain(self, chain_events: list) -> list[Pattern]:
        """从完整事件链中提取可复用模式"""
        new_patterns = []

        for i, event in enumerate(chain_events):
            if event.event_type in ("DEFENSE_REPORT", "CRAWL_STRATEGY"):
                keywords = self._extract_keywords(event.body)
                pattern = Pattern(
                    pattern_id=f"pat-{event.event_id[:8]}",
                    event_type=chain_events[i - 1].event_type if i > 0 else event.event_type,
                    context_keywords=keywords,
                    source_team=event.source_team,
                    solution_summary=event.body[:500],
                    solution_path=f"events/resolved/{event.event_id[:8]}",
                    confidence=0.7,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    chain_shortcut={
                        "skip_event_types": [event.event_type],
                        "direct_to_team": event.metadata.get("callback", {}).get("team", "") if event.metadata.get("callback") else "",
                    },
                )
                new_patterns.append(pattern)

            if event.event_type == "DATA_READY":
                keywords = self._extract_keywords(event.body)
                pattern = Pattern(
                    pattern_id=f"pat-{event.event_id[:8]}",
                    event_type="DATA_GAP",
                    context_keywords=keywords,
                    source_team=event.source_team,
                    solution_summary=f"Previously collected data: {event.body[:300]}",
                    solution_path=f"events/resolved/{event.event_id[:8]}",
                    confidence=0.5,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    chain_shortcut={},
                )
                new_patterns.append(pattern)

        self.patterns.extend(new_patterns)
        self._save()
        return new_patterns

    def find_shortcut(self, event_type: str, context: str) -> Pattern | None:
        """查找是否有可复用的模式可以跳步"""
        candidates = [p for p in self.patterns
                      if p.event_type == event_type
                      and p.confidence >= self.CONFIDENCE_THRESHOLD]

        if not candidates:
            return None

        context_lower = context.lower()
        scored = []
        for p in candidates:
            keyword_hits = sum(1 for kw in p.context_keywords if kw.lower() in context_lower)
            score = keyword_hits * 0.6 + p.confidence * 0.4
            if keyword_hits > 0:
                scored.append((score, p))

        if not scored:
            return None

        scored.sort(key=lambda x: -x[0])
        return scored[0][1]

    def record_usage(self, pattern_id: str, success: bool):
        """记录模式使用结果，更新置信度"""
        for p in self.patterns:
            if p.pattern_id == pattern_id:
                if success:
                    p.success_count += 1
                else:
                    p.fail_count += 1
                total = p.success_count + p.fail_count
                p.confidence = (p.success_count + 1) / (total + 2)  # Laplace smoothing
                p.last_used_at = datetime.now(timezone.utc).isoformat()
                self._save()
                return

    def evolve_after_chain(self, chain_prefix: str):
        """链路完成后触发进化"""
        resolved_dir = self.workspace_dir / "events" / "resolved"
        if not resolved_dir.exists():
            return []

        from .event import Event
        chain_events = []
        for f in sorted(resolved_dir.glob("*.md")):
            try:
                event = Event.from_file(f)
                if chain_prefix.lower() in event.event_id.lower():
                    chain_events.append(event)
            except Exception:
                continue

        if len(chain_events) < 2:
            return []

        chain_events.sort(key=lambda e: e.chain_depth)

        new_patterns = self.extract_from_chain(chain_events)
        if new_patterns:
            try:
                from .memory_bridge import MemoryBridge
                mb = MemoryBridge(self.workspace_dir)
                for p in new_patterns:
                    mb.store(
                        domain="patterns",
                        topic=p.pattern_id,
                        content=f"# Pattern: {p.pattern_id}\n\nEvent: {p.event_type}\nKeywords: {', '.join(p.context_keywords)}\nTeam: {p.source_team}\nConfidence: {p.confidence}\n\n{p.solution_summary}",
                        source_team=p.source_team,
                        tags=["auto-evolved", p.event_type],
                    )
            except Exception as e:
                logger.warning(f"Failed to write to MemoryBridge: {e}")

        logger.info(f"Evolved {len(new_patterns)} patterns from chain '{chain_prefix}'")
        return new_patterns

    def _extract_keywords(self, text: str) -> list[str]:
        """从文本中提取关键词"""
        if not text:
            return []
        en_words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        cn_patterns = re.findall(r'[\u4e00-\u9fff]{2,4}', text)

        stopwords = {"this", "that", "with", "from", "have", "been", "will", "need",
                     "data", "team", "event", "mode", "的", "了", "在", "是", "和", "有"}
        keywords = list(set(w for w in en_words + cn_patterns if w not in stopwords))
        return keywords[:20]

    def format_patterns(self) -> str:
        """格式化输出所有模式"""
        if not self.patterns:
            return "No evolved patterns yet."

        lines = ["━━━━━ Evolved Patterns ━━━━━"]
        lines.append(f"Total: {len(self.patterns)}\n")

        for p in sorted(self.patterns, key=lambda x: -x.confidence):
            status = "🟢" if p.confidence >= self.CONFIDENCE_THRESHOLD else "🟡"
            lines.append(f"{status} {p.pattern_id} [{p.event_type}] conf={p.confidence:.2f}")
            lines.append(f"   Keywords: {', '.join(p.context_keywords[:5])}")
            lines.append(f"   Used: {p.success_count}✅ {p.fail_count}❌")
            if p.chain_shortcut:
                lines.append(f"   Shortcut: skip {p.chain_shortcut.get('skip_event_types', [])}")
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    def _load(self):
        if self.patterns_path.exists():
            try:
                data = json.loads(self.patterns_path.read_text())
                self.patterns = [Pattern(**d) for d in data]
            except Exception as e:
                logger.warning(f"Failed to load patterns: {e}")

    def _save(self):
        self.patterns_path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(p) for p in self.patterns]
        self.patterns_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

"""
Memory Bridge — 跨团队知识共享。
团队产出的关键结论自动写入共享知识库，其他团队处理事件前先查知识库避免重复劳动。
"""
from pathlib import Path
from datetime import datetime, timezone
import json, logging

logger = logging.getLogger(__name__)


class MemoryBridge:
    KNOWLEDGE_DIR = "knowledge"

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.knowledge_dir = workspace_dir / self.KNOWLEDGE_DIR

    def store(self, domain: str, topic: str, content: str, source_team: str, tags: list[str] = None):
        """存储知识条目"""
        path = self.knowledge_dir / domain / f"{topic}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        header = f"""---
source_team: {source_team}
updated_at: {datetime.now(timezone.utc).isoformat()}
tags: {json.dumps(tags or [], ensure_ascii=False)}
---

"""
        path.write_text(header + content)
        logger.info(f"Stored knowledge: {domain}/{topic} from {source_team}")

    def query(self, domain: str = None, topic: str = None, tag: str = None) -> list[dict]:
        """查询知识库"""
        results = []
        if not self.knowledge_dir.exists():
            return results

        search_dirs = [self.knowledge_dir / domain] if domain else [
            d for d in self.knowledge_dir.iterdir() if d.is_dir()
        ]

        for d in search_dirs:
            if not d.is_dir():
                continue
            for f in d.glob("*.md"):
                if topic and topic.lower() not in f.stem.lower():
                    continue
                content = f.read_text()
                meta = self._parse_header(content)
                if tag and tag not in meta.get("tags", []):
                    continue
                results.append({
                    "domain": d.name,
                    "topic": f.stem,
                    "path": str(f.relative_to(self.workspace_dir)),
                    "source_team": meta.get("source_team", "unknown"),
                    "updated_at": meta.get("updated_at", ""),
                    "preview": content.split("---", 2)[-1].strip()[:200] if "---" in content else content[:200],
                })
        return results

    def query_for_event(self, event_type: str, context: str = "") -> list[dict]:
        """根据事件类型和上下文查找相关知识"""
        domain_map = {
            "CRAWL_BLOCKED": "defense",
            "CRAWL_STRATEGY": "defense",
            "SECURITY_INCIDENT": "defense",
            "DATA_GAP": "data",
            "DATA_READY": "data",
            "MARKET_SIGNAL": "market",
            "ANOMALY": "data",
            "DEFENSE_REPORT": "defense",
        }
        domain = domain_map.get(event_type)
        results = self.query(domain=domain)

        if context and results:
            keywords = set(context.lower().split())
            scored = []
            for r in results:
                preview_words = set(r["preview"].lower().split())
                overlap = len(keywords & preview_words)
                scored.append((overlap, r))
            scored.sort(key=lambda x: -x[0])
            return [r for s, r in scored if s > 0] or results[:5]

        return results[:5]

    def format_for_prompt(self, results: list[dict]) -> str:
        """格式化知识条目为sub-agent可读文本"""
        if not results:
            return "(no relevant knowledge found)"
        lines = ["## Shared Knowledge Base"]
        for r in results:
            lines.append(f"### [{r['domain']}] {r['topic']} (from {r['source_team']})")
            lines.append(r["preview"])
            lines.append(f"Full: {r['path']}\n")
        return "\n".join(lines)

    def _parse_header(self, content: str) -> dict:
        """解析YAML头部"""
        import yaml
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    return yaml.safe_load(parts[1]) or {}
                except Exception:
                    pass
        return {}

    def list_domains(self) -> list[str]:
        """列出所有知识域"""
        if not self.knowledge_dir.exists():
            return []
        return [d.name for d in self.knowledge_dir.iterdir() if d.is_dir()]

    def stats(self) -> dict:
        """知识库统计"""
        total = 0
        by_domain = {}
        for domain in self.list_domains():
            count = len(list((self.knowledge_dir / domain).glob("*.md")))
            by_domain[domain] = count
            total += count
        return {"total": total, "by_domain": by_domain}

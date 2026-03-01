"""
DataBus — 跨团队数据交换层。

解决的问题：团队A采集了数据，团队B怎么知道去哪读、格式是什么。
方案：事件中嵌入data_refs，DataBus负责解析、验证、查找。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import logging

logger = logging.getLogger(__name__)

# 内置Schema定义
BUILTIN_SCHEMAS: dict[str, dict[str, Any]] = {
    "product_price_v1": {
        "description": "产品价格数据",
        "required_fields": ["title", "price"],
        "optional_fields": ["sales", "url", "supplier", "rating", "reviews"],
        "formats": ["json", "jsonl", "csv"],
    },
    "supplier_price_v1": {
        "description": "供应商出厂价数据",
        "required_fields": ["title", "price", "supplier"],
        "optional_fields": ["moq", "url", "specs", "location"],
        "formats": ["json", "jsonl", "csv"],
    },
    "defense_report_v1": {
        "description": "ARC防御评估报告",
        "required_fields": ["platform", "defense_level", "strategy"],
        "optional_fields": ["confidence", "tools", "bypass_methods"],
        "formats": ["json", "md"],
    },
    "crawl_result_v1": {
        "description": "采集结果元数据",
        "required_fields": ["total_items", "success_count", "output_path"],
        "optional_fields": ["fail_count", "blocked_pages", "duration_seconds"],
        "formats": ["json"],
    },
}


@dataclass
class DataRef:
    """数据引用 — 指向workspace中某个数据文件，附带类型和Schema信息。"""

    ref_type: str          # "json" | "jsonl" | "csv" | "md" | "dir"
    path: str              # 相对于workspace的路径
    schema: str = ""       # Schema名称（如 product_price_v1）
    description: str = ""  # 人类可读描述
    record_count: int = 0  # 记录数（可选）

    def resolve(self, workspace_dir: Path) -> Path:
        """解析为绝对路径。"""
        return workspace_dir / self.path

    def exists(self, workspace_dir: Path) -> bool:
        """检查数据文件是否存在。"""
        return self.resolve(workspace_dir).exists()

    def validate(self, workspace_dir: Path) -> tuple[bool, str]:
        """验证数据文件是否符合Schema。"""
        full_path = self.resolve(workspace_dir)
        if not full_path.exists():
            return False, f"File not found: {self.path}"

        if not self.schema or self.schema not in BUILTIN_SCHEMAS:
            return True, "No schema to validate against"

        schema_def = BUILTIN_SCHEMAS[self.schema]

        if self.ref_type == "json":
            try:
                data = json.loads(full_path.read_text(encoding="utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    sample = data[0]
                elif isinstance(data, dict):
                    sample = data
                else:
                    return True, "Empty or non-dict data, skipping field check"

                missing = [f for f in schema_def["required_fields"] if f not in sample]
                if missing:
                    return False, f"Missing required fields: {missing}"
                return True, f"Valid: {len(data) if isinstance(data, list) else 1} records"
            except json.JSONDecodeError as e:
                return False, f"Invalid JSON: {e}"

        return True, f"Format {self.ref_type} not validated"

    def to_dict(self) -> dict[str, Any]:
        """序列化为dict（用于YAML front-matter）。"""
        d: dict[str, Any] = {"type": self.ref_type, "path": self.path}
        if self.schema:
            d["schema"] = self.schema
        if self.description:
            d["description"] = self.description
        if self.record_count:
            d["record_count"] = self.record_count
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DataRef:
        """从dict反序列化。"""
        return cls(
            ref_type=d.get("type", "json"),
            path=d["path"],
            schema=d.get("schema", ""),
            description=d.get("description", ""),
            record_count=d.get("record_count", 0),
        )


class DataBus:
    """数据交换总线。

    职责：
    1. 解析事件中的data_refs
    2. 验证数据文件存在性和Schema合规性
    3. 提供数据查找功能（按team、schema查找可用数据）
    4. 管理Schema注册表
    """

    def __init__(self, workspace_dir: Path) -> None:
        self.workspace_dir = workspace_dir
        self.schemas: dict[str, dict[str, Any]] = dict(BUILTIN_SCHEMAS)
        self._load_custom_schemas()

    def _load_custom_schemas(self) -> None:
        """加载自定义Schema（从workspace/schemas/目录）。"""
        schema_dir = self.workspace_dir / "schemas"
        if not schema_dir.exists():
            return
        for f in schema_dir.glob("*.json"):
            try:
                custom = json.loads(f.read_text(encoding="utf-8"))
                self.schemas[f.stem] = custom
                logger.debug("Loaded custom schema: %s", f.stem)
            except Exception as e:
                logger.warning("Failed to load schema %s: %s", f, e)

    def parse_refs(self, event: Any) -> list[DataRef]:
        """从事件中提取data_refs。"""
        refs_raw = getattr(event, "data_refs", None)
        if not refs_raw:
            return []
        return [DataRef.from_dict(d) for d in refs_raw]

    def validate_refs(self, refs: list[DataRef]) -> list[tuple[DataRef, bool, str]]:
        """批量验证数据引用。"""
        return [(ref, *ref.validate(self.workspace_dir)) for ref in refs]

    def find_data(self, team: str | None = None, schema: str | None = None) -> list[DataRef]:
        """按条件查找可用数据。"""
        results: list[DataRef] = []
        search_dirs: list[tuple[str, Path]] = []

        if team:
            warehouse = self.workspace_dir / team / "warehouse" / "cleaned"
            if warehouse.exists():
                search_dirs.append((team, warehouse))
        else:
            for team_dir in self.workspace_dir.iterdir():
                if team_dir.is_dir() and (team_dir / "ORCHESTRATOR.md").exists():
                    warehouse = team_dir / "warehouse" / "cleaned"
                    if warehouse.exists():
                        search_dirs.append((team_dir.name, warehouse))

        for team_name, warehouse in search_dirs:
            for f in warehouse.glob("*.json"):
                ref = DataRef(
                    ref_type="json",
                    path=str(f.relative_to(self.workspace_dir)),
                    description=f"Auto-discovered from {team_name}",
                )
                if schema:
                    ref.schema = schema
                    valid, _ = ref.validate(self.workspace_dir)
                    if valid:
                        results.append(ref)
                else:
                    results.append(ref)

        return results

    def list_schemas(self) -> dict[str, str]:
        """列出所有可用Schema。"""
        return {k: v.get("description", "") for k, v in self.schemas.items()}

    def format_refs_for_prompt(self, refs: list[DataRef]) -> str:
        """将data_refs格式化为sub-agent可读的文本。"""
        if not refs:
            return "(no data references)"
        lines = ["## Available Data References"]
        for i, ref in enumerate(refs, 1):
            status = "✅" if ref.exists(self.workspace_dir) else "❌"
            lines.append(f"{i}. {status} [{ref.ref_type}] {ref.path}")
            if ref.schema:
                lines.append(f"   Schema: {ref.schema}")
            if ref.description:
                lines.append(f"   {ref.description}")
        return "\n".join(lines)

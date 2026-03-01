"""
Team Capability Registry — 动态发现团队能力，自动构建路由表。

扫描所有团队的capabilities.yaml → 构建event_type → team/mode映射。
新团队只需要放一个capabilities.yaml，零代码改动即可接入Event Bus。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import logging
import yaml

logger = logging.getLogger(__name__)


@dataclass
class Capability:
    team: str
    event_type: str
    modes: list[str]
    description: str = ""
    priority: int = 0  # 多个团队能处理同一事件时，priority高的优先


@dataclass
class TeamInfo:
    name: str
    description: str
    capabilities: list[Capability] = field(default_factory=list)


class Registry:
    """Scan capabilities.yaml files and build a dynamic route table."""

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.teams: dict[str, TeamInfo] = {}
        # route_table uses same format as Router: event_type → {"target_team", "target_mode"}
        self.route_table: dict[str, dict[str, str]] = {}

    def scan(self) -> int:
        """扫描所有团队的capabilities.yaml，返回发现的团队数"""
        self.teams.clear()
        self.route_table.clear()
        count = 0

        # 搜索路径：workspace下所有*-team目录 + examples/*-team + teams/*
        search_paths = (
            list(self.workspace_dir.glob("*-team"))
            + list(self.workspace_dir.glob("examples/*-team"))
            + list(self.workspace_dir.glob("teams/*"))
        )

        for team_dir in search_paths:
            cap_file = team_dir / "capabilities.yaml"
            if cap_file.exists():
                try:
                    info = self._parse_capabilities(cap_file)
                    self.teams[info.name] = info
                    self._register_routes(info)
                    count += 1
                    logger.info("Registered team: %s (%d capabilities)", info.name, len(info.capabilities))
                except Exception as e:
                    logger.warning("Failed to parse %s: %s", cap_file, e)

        return count

    def _parse_capabilities(self, path: Path) -> TeamInfo:
        """解析capabilities.yaml"""
        data = yaml.safe_load(path.read_text())
        caps = []
        for c in data.get("capabilities", []):
            caps.append(Capability(
                team=data["team"],
                event_type=c["event_type"],
                modes=c.get("modes", ["A"]),
                description=c.get("description", ""),
                priority=c.get("priority", 0),
            ))
        return TeamInfo(
            name=data["team"],
            description=data.get("description", ""),
            capabilities=caps,
        )

    def _register_routes(self, info: TeamInfo) -> None:
        """将能力注册到路由表"""
        for cap in info.capabilities:
            existing = self.route_table.get(cap.event_type)
            if existing is None:
                self.route_table[cap.event_type] = {
                    "target_team": cap.team,
                    "target_mode": cap.modes[0],
                }
            else:
                # priority高的覆盖
                existing_team = self.teams.get(existing["target_team"])
                if existing_team:
                    existing_cap = next(
                        (c for c in existing_team.capabilities if c.event_type == cap.event_type),
                        None,
                    )
                    if existing_cap and cap.priority > existing_cap.priority:
                        self.route_table[cap.event_type] = {
                            "target_team": cap.team,
                            "target_mode": cap.modes[0],
                        }

    def get_route(self, event_type: str) -> dict[str, str] | None:
        """查询事件路由"""
        return self.route_table.get(event_type)

    def get_all_routes(self) -> dict[str, dict[str, str]]:
        """获取完整路由表（与Router格式兼容）"""
        return dict(self.route_table)

    def get_team_info(self, team: str) -> TeamInfo | None:
        """获取团队信息"""
        return self.teams.get(team)

    def format_registry(self) -> str:
        """格式化输出注册表"""
        lines = ["━━━━━ Team Capability Registry ━━━━━"]
        lines.append(f"Teams: {len(self.teams)} | Routes: {len(self.route_table)}\n")

        for name, info in sorted(self.teams.items()):
            lines.append(f"📋 {name}: {info.description}")
            for cap in info.capabilities:
                modes_str = "/".join(cap.modes)
                lines.append(f"   {cap.event_type} → Mode {modes_str}: {cap.description}")
            lines.append("")

        lines.append("Route Table:")
        for event_type, route in sorted(self.route_table.items()):
            lines.append(f"  {event_type} → {route['target_team']} (Mode {route['target_mode']})")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

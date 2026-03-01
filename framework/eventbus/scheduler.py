"""
Chain Scheduler — 多链路并行调度。

支持同时运行多条独立事件链，共享团队资源时的并发控制。
"""
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChainState:
    """事件链状态"""
    chain_id: str            # 链路ID（通常是event_id前缀）
    status: str              # "active" | "paused" | "completed" | "failed"
    started_at: str = ""
    events: list[str] = field(default_factory=list)  # 该链路的event_id列表
    current_step: int = 0    # 当前步骤
    total_steps: int = 0     # 总步骤（预估）
    priority: int = 0        # 链路优先级
    team_locks: list[str] = field(default_factory=list)  # 当前锁定的团队


@dataclass
class TeamLock:
    """团队锁"""
    team: str
    chain_id: str
    locked_at: str
    mode: str


class Scheduler:
    STATE_FILE = ".watchdog/scheduler.json"
    MAX_CONCURRENT_CHAINS = 5      # 最大并行链路数
    MAX_TEAM_CONCURRENCY = 1       # 每个团队同时处理的最大链路数（默认1，串行）

    def __init__(self, workspace_dir: Path, config: dict = None):
        self.workspace_dir = workspace_dir
        self.state_path = workspace_dir / "events" / self.STATE_FILE
        self.chains: dict[str, ChainState] = {}
        self.team_locks: dict[str, list[TeamLock]] = {}  # team → [locks]
        self.config = config or {}
        self.max_concurrent = self.config.get("max_concurrent_chains", self.MAX_CONCURRENT_CHAINS)
        self.max_team_concurrency = self.config.get("max_team_concurrency", self.MAX_TEAM_CONCURRENCY)
        self._load()

    def can_start_chain(self) -> tuple[bool, str]:
        """检查是否可以启动新链路"""
        active = sum(1 for c in self.chains.values() if c.status == "active")
        if active >= self.max_concurrent:
            return False, f"Max concurrent chains reached ({active}/{self.max_concurrent})"
        return True, f"OK ({active}/{self.max_concurrent} active)"

    def can_dispatch_to_team(self, team: str, chain_id: str) -> tuple[bool, str]:
        """检查团队是否可以接受新任务"""
        locks = self.team_locks.get(team, [])
        # 排除同一链路的锁（允许同一链路在同一团队的不同步骤）
        other_locks = [l for l in locks if l.chain_id != chain_id]
        if len(other_locks) >= self.max_team_concurrency:
            blocking = [l.chain_id for l in other_locks]
            return False, f"Team {team} busy (locked by {blocking})"
        return True, "OK"

    def register_chain(self, chain_id: str, priority: int = 0) -> ChainState:
        """注册新链路"""
        if chain_id in self.chains:
            return self.chains[chain_id]
        state = ChainState(
            chain_id=chain_id,
            status="active",
            started_at=datetime.now(timezone.utc).isoformat(),
            priority=priority,
        )
        self.chains[chain_id] = state
        self._save()
        logger.info(f"Chain registered: {chain_id}")
        return state

    def acquire_team_lock(self, team: str, chain_id: str, mode: str) -> bool:
        """获取团队锁"""
        can, msg = self.can_dispatch_to_team(team, chain_id)
        if not can:
            logger.warning(f"Cannot lock {team}: {msg}")
            return False

        lock = TeamLock(
            team=team,
            chain_id=chain_id,
            locked_at=datetime.now(timezone.utc).isoformat(),
            mode=mode,
        )
        if team not in self.team_locks:
            self.team_locks[team] = []
        self.team_locks[team].append(lock)

        # 更新chain状态
        if chain_id in self.chains:
            self.chains[chain_id].team_locks.append(team)

        self._save()
        logger.info(f"Team lock acquired: {team} by {chain_id}")
        return True

    def release_team_lock(self, team: str, chain_id: str):
        """释放团队锁"""
        if team in self.team_locks:
            self.team_locks[team] = [l for l in self.team_locks[team] if l.chain_id != chain_id]

        if chain_id in self.chains:
            self.chains[chain_id].team_locks = [t for t in self.chains[chain_id].team_locks if t != team]

        self._save()
        logger.info(f"Team lock released: {team} by {chain_id}")

    def add_event_to_chain(self, chain_id: str, event_id: str):
        """记录事件到链路"""
        if chain_id in self.chains:
            self.chains[chain_id].events.append(event_id)
            self.chains[chain_id].current_step = len(self.chains[chain_id].events)
            self._save()

    def complete_chain(self, chain_id: str):
        """完成链路"""
        if chain_id in self.chains:
            self.chains[chain_id].status = "completed"
            # 释放所有团队锁
            for team in list(self.chains[chain_id].team_locks):
                self.release_team_lock(team, chain_id)
            self._save()
            logger.info(f"Chain completed: {chain_id}")

    def fail_chain(self, chain_id: str, reason: str = ""):
        """标记链路失败"""
        if chain_id in self.chains:
            self.chains[chain_id].status = "failed"
            for team in list(self.chains[chain_id].team_locks):
                self.release_team_lock(team, chain_id)
            self._save()
            logger.warning(f"Chain failed: {chain_id} - {reason}")

    def get_queue_position(self, chain_id: str) -> int:
        """获取链路在等待队列中的位置"""
        active = [(c.priority, c.started_at, cid) for cid, c in self.chains.items() if c.status == "active"]
        active.sort(key=lambda x: (-x[0], x[1]))
        for i, (_, _, cid) in enumerate(active):
            if cid == chain_id:
                return i
        return -1

    def format_status(self) -> str:
        """格式化调度器状态"""
        lines = ["━━━━━ Chain Scheduler ━━━━━"]
        active = [c for c in self.chains.values() if c.status == "active"]
        completed = [c for c in self.chains.values() if c.status == "completed"]
        failed = [c for c in self.chains.values() if c.status == "failed"]

        lines.append(f"Active: {len(active)}/{self.max_concurrent} | Completed: {len(completed)} | Failed: {len(failed)}\n")

        if active:
            lines.append("Active Chains:")
            for c in active:
                locks = ", ".join(c.team_locks) if c.team_locks else "none"
                lines.append(f"  🔄 {c.chain_id} step={c.current_step} locks=[{locks}]")

        # 团队锁状态
        lines.append("\nTeam Locks:")
        all_teams: set[str] = set()
        for team_dir in self.workspace_dir.iterdir():
            if team_dir.is_dir() and (team_dir / "ORCHESTRATOR.md").exists():
                all_teams.add(team_dir.name)
        examples_dir = self.workspace_dir / "examples"
        if examples_dir.exists():
            for team_dir in examples_dir.iterdir():
                if team_dir.is_dir() and (team_dir / "ORCHESTRATOR.md").exists():
                    all_teams.add(team_dir.name)

        for team in sorted(all_teams):
            locks = self.team_locks.get(team, [])
            status = "🔒 " + ", ".join(l.chain_id for l in locks) if locks else "🟢 available"
            lines.append(f"  {team}: {status}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    def _load(self):
        if not self.state_path.exists():
            return
        try:
            data = json.loads(self.state_path.read_text())
            for cid, d in data.get("chains", {}).items():
                self.chains[cid] = ChainState(**d)
            for team, locks in data.get("team_locks", {}).items():
                self.team_locks[team] = [TeamLock(**l) for l in locks]
        except Exception as e:
            logger.warning(f"Failed to load scheduler state: {e}")

    def _save(self):
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        from dataclasses import asdict
        data = {
            "chains": {cid: asdict(c) for cid, c in self.chains.items()},
            "team_locks": {team: [asdict(l) for l in locks] for team, locks in self.team_locks.items()},
        }
        self.state_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

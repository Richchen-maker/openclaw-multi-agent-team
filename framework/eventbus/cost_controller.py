"""
Cost Controller — 控制跨团队协作的token消耗。
severity → model映射，链路预算控制，超预算暂停。
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import json, logging

logger = logging.getLogger(__name__)

# 模型成本估算（每1K token，美元）
MODEL_COSTS = {
    "anthropic/claude-opus-4-6": 0.075,
    "anthropic/claude-sonnet-4-20250514": 0.015,
    "anthropic/claude-haiku-3-20240307": 0.001,
    "default": 0.015,
}

# severity → 推荐模型
SEVERITY_MODEL_MAP = {
    "CRITICAL": None,
    "HIGH": None,
    "MEDIUM": "anthropic/claude-sonnet-4-20250514",
    "LOW": "anthropic/claude-sonnet-4-20250514",
}


@dataclass
class ChainBudget:
    chain_id: str
    max_tokens: int
    used_tokens: int = 0
    max_cost_usd: float = 0
    used_cost_usd: float = 0
    paused: bool = False

    @property
    def remaining_tokens(self) -> int:
        return max(0, self.max_tokens - self.used_tokens)

    @property
    def usage_pct(self) -> float:
        return (self.used_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0


class CostController:
    BUDGET_FILE = ".watchdog/budgets.json"
    DEFAULT_CHAIN_BUDGET = 100000

    def __init__(self, workspace_dir: Path):
        self.workspace_dir = workspace_dir
        self.budget_path = workspace_dir / "events" / self.BUDGET_FILE
        self.budgets: dict[str, ChainBudget] = {}
        self._load()

    def get_model_for_severity(self, severity: str) -> str | None:
        """根据severity返回推荐模型，None=使用默认"""
        return SEVERITY_MODEL_MAP.get(severity)

    def check_budget(self, chain_id: str) -> tuple[bool, str]:
        """检查链路预算是否允许继续"""
        budget = self.budgets.get(chain_id)
        if budget is None:
            budget = ChainBudget(chain_id=chain_id, max_tokens=self.DEFAULT_CHAIN_BUDGET)
            self.budgets[chain_id] = budget
            self._save()
            return True, f"New chain budget: {budget.max_tokens} tokens"

        if budget.paused:
            return False, f"Chain {chain_id} paused (used {budget.used_tokens}/{budget.max_tokens})"

        if budget.used_tokens >= budget.max_tokens:
            budget.paused = True
            self._save()
            return False, f"Chain {chain_id} over budget ({budget.usage_pct:.0f}%)"

        if budget.usage_pct >= 80:
            return True, f"WARNING: Chain {chain_id} at {budget.usage_pct:.0f}% budget"

        return True, "OK"

    def record_usage(self, chain_id: str, tokens: int):
        """记录token使用"""
        if chain_id not in self.budgets:
            self.budgets[chain_id] = ChainBudget(chain_id=chain_id, max_tokens=self.DEFAULT_CHAIN_BUDGET)
        budget = self.budgets[chain_id]
        budget.used_tokens += tokens
        cost_rate = MODEL_COSTS.get("default", 0.015)
        budget.used_cost_usd += tokens / 1000 * cost_rate
        self._save()

    def set_budget(self, chain_id: str, max_tokens: int):
        """设置链路预算"""
        if chain_id not in self.budgets:
            self.budgets[chain_id] = ChainBudget(chain_id=chain_id, max_tokens=max_tokens)
        else:
            self.budgets[chain_id].max_tokens = max_tokens
            self.budgets[chain_id].paused = False
        self._save()

    def resume_chain(self, chain_id: str):
        """恢复被暂停的链路"""
        if chain_id in self.budgets:
            self.budgets[chain_id].paused = False
            self._save()

    def format_report(self) -> str:
        """成本报告"""
        lines = ["━━━━━ Cost Controller ━━━━━"]
        total_tokens = sum(b.used_tokens for b in self.budgets.values())
        total_cost = sum(b.used_cost_usd for b in self.budgets.values())
        lines.append(f"Total: {total_tokens:,} tokens (~${total_cost:.3f})\n")

        for cid, b in sorted(self.budgets.items()):
            status = "⏸️ PAUSED" if b.paused else "✅ active"
            bar_len = int(b.usage_pct / 10)
            bar = "■" * bar_len + "□" * (10 - bar_len)
            lines.append(f"  {cid}: {b.used_tokens:,}/{b.max_tokens:,} ({b.usage_pct:.0f}%) {bar} {status}")
            lines.append(f"    Cost: ~${b.used_cost_usd:.3f}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
        return "\n".join(lines)

    def _load(self):
        if self.budget_path.exists():
            try:
                data = json.loads(self.budget_path.read_text())
                for cid, d in data.items():
                    self.budgets[cid] = ChainBudget(**d)
            except Exception as e:
                logger.warning(f"Failed to load budgets: {e}")

    def _save(self):
        self.budget_path.parent.mkdir(parents=True, exist_ok=True)
        data = {cid: asdict(b) for cid, b in self.budgets.items()}
        self.budget_path.write_text(json.dumps(data, indent=2))

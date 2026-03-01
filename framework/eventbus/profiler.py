"""
Performance Profiler — 追踪每个团队和事件类型的性能指标。

基于history.jsonl构建系统画像，识别瓶颈和退化趋势。
"""

from __future__ import annotations

import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# 基线：processing的标准耗时（秒）
BASELINE_PROCESSING_SECONDS = 120.0


@dataclass
class TeamProfile:
    """团队性能画像。"""

    team_name: str
    total_events: int = 0
    success_count: int = 0
    fail_count: int = 0
    avg_processing_seconds: float = 0.0
    max_processing_seconds: float = 0.0
    success_rate: float = 0.0
    health_score: int = 100
    bottleneck_event_type: str = ""
    trend: str = "stable"  # improving / stable / degrading


@dataclass
class EventTypeProfile:
    """事件类型性能画像。"""

    event_type: str
    total: int = 0
    avg_chain_time_seconds: float = 0.0
    failure_rate: float = 0.0
    most_common_failure: str = ""


@dataclass
class SystemProfile:
    """系统整体画像。"""

    overall_score: int = 100
    teams: dict[str, TeamProfile] = field(default_factory=dict)
    event_types: dict[str, EventTypeProfile] = field(default_factory=dict)
    throughput_per_hour: float = 0.0
    avg_chain_completion_seconds: float = 0.0
    bottleneck_team: str = ""
    pending_velocity: float = 0.0
    consume_velocity: float = 0.0


class Profiler:
    """基于Watchdog历史数据构建性能画像。"""

    HISTORY_FILE = ".watchdog/history.jsonl"

    def __init__(self, workspace_dir: Path) -> None:
        self.workspace_dir = workspace_dir
        self.events_dir = workspace_dir / "events"
        self.history_path = self.events_dir / self.HISTORY_FILE

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def build_profile(self, window_hours: int = 24) -> SystemProfile:
        """基于历史数据构建系统画像。"""
        records = self._load_records(window_hours)
        if not records:
            return SystemProfile()

        profile = SystemProfile()

        # 聚合团队数据
        team_data: dict[str, list[dict]] = {}
        event_type_data: dict[str, list[dict]] = {}

        for rec in records:
            # 从alerts提取团队+事件类型信息
            for alert in rec.get("alerts", []):
                msg = alert.get("message", "")
                team = self._extract_team_from_alert(alert)
                etype = self._extract_event_type_from_alert(alert)
                if team:
                    team_data.setdefault(team, []).append(alert)
                if etype:
                    event_type_data.setdefault(etype, []).append(alert)

            # 从team_scores提取健康分
            for team, score in rec.get("team_scores", {}).items():
                if team not in profile.teams:
                    profile.teams[team] = TeamProfile(team_name=team)
                profile.teams[team].health_score = score

        # 从recoveries聚合成功/失败
        total_resolved = 0
        total_failed = 0
        pending_counts: list[int] = []

        for rec in records:
            total_resolved += rec.get("resolved_count", 0)
            total_failed += rec.get("failed_count", 0)
            pending_counts.append(rec.get("pending_count", 0))
            for recovery in rec.get("recoveries", []):
                team = recovery.get("team", "")
                if team and team in profile.teams:
                    if recovery.get("success"):
                        profile.teams[team].success_count += 1
                    else:
                        profile.teams[team].fail_count += 1

        # 吞吐量
        hours = max(window_hours, 1)
        profile.throughput_per_hour = total_resolved / hours

        # pending速度
        if len(pending_counts) >= 2:
            profile.pending_velocity = (pending_counts[-1] - pending_counts[0]) / hours
        profile.consume_velocity = profile.throughput_per_hour

        # 团队健康计算
        for team_name, tp in profile.teams.items():
            tp.total_events = tp.success_count + tp.fail_count
            tp.success_rate = tp.success_count / tp.total_events if tp.total_events else 1.0
            tp.health_score = self.calculate_team_health(team_name, window_hours)

        # 瓶颈
        profile.bottleneck_team = self.detect_bottleneck(profile)

        # 整体评分：所有团队健康分的加权平均
        if profile.teams:
            scores = [t.health_score for t in profile.teams.values()]
            profile.overall_score = int(sum(scores) / len(scores))

        return profile

    def calculate_team_health(self, team: str, window_hours: int = 24) -> int:
        """计算团队健康评分 0-100。

        权重：
        - 响应速度 40%: avg_processing vs BASELINE
        - 成功率 40%: success / total
        - 稳定性 20%: 低方差=高分
        """
        records = self._load_records(window_hours)
        if not records:
            return 100

        processing_times: list[float] = []
        successes = 0
        failures = 0

        for rec in records:
            for alert in rec.get("alerts", []):
                t = self._extract_team_from_alert(alert)
                if t != team:
                    continue
                # 从message中提取处理时间
                age = self._extract_age_from_message(alert.get("message", ""))
                if age is not None:
                    processing_times.append(age)
                if alert.get("check_type") in ("STALE_PROCESSING", "CHAIN_BROKEN"):
                    failures += 1
                else:
                    successes += 1

        total = successes + failures

        # 响应速度分 (40%)
        if processing_times:
            avg_time = sum(processing_times) / len(processing_times)
            speed_ratio = min(avg_time / BASELINE_PROCESSING_SECONDS, 5.0)
            speed_score = max(0, 100 - int(speed_ratio * 20))
        else:
            speed_score = 100

        # 成功率分 (40%)
        if total > 0:
            rate_score = int((successes / total) * 100)
        else:
            rate_score = 100

        # 稳定性分 (20%)
        if len(processing_times) >= 2:
            mean = sum(processing_times) / len(processing_times)
            variance = sum((x - mean) ** 2 for x in processing_times) / len(processing_times)
            std = math.sqrt(variance)
            cv = std / mean if mean > 0 else 0  # 变异系数
            stability_score = max(0, 100 - int(cv * 50))
        else:
            stability_score = 100

        return int(speed_score * 0.4 + rate_score * 0.4 + stability_score * 0.2)

    def detect_bottleneck(self, profile: SystemProfile) -> str:
        """检测系统瓶颈：健康分最低的团队。"""
        if not profile.teams:
            return ""

        worst_team = ""
        worst_score = 101

        for name, tp in profile.teams.items():
            if tp.health_score < worst_score:
                worst_score = tp.health_score
                worst_team = name

        # 只有分数低于70才算瓶颈
        if worst_score < 70:
            logger.info("Bottleneck detected: team=%s score=%d", worst_team, worst_score)
            return worst_team
        return ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_records(self, window_hours: int) -> list[dict]:
        """从history.jsonl加载指定时间窗口内的记录。"""
        if not self.history_path.exists():
            return []

        cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        results: list[dict] = []

        try:
            for line in self.history_path.read_text(encoding="utf-8").strip().splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    ts = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                    if ts >= cutoff:
                        results.append(data)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        except Exception as e:
            logger.error("Failed to load history: %s", e)
        return results

    @staticmethod
    def _extract_team_from_alert(alert: dict) -> str:
        """从alert message中提取team名。"""
        msg = alert.get("message", "")
        # 常见格式: "...team=xxx..." 或 "...team={name}..."
        for prefix in ("team=", "source_team="):
            if prefix in msg:
                start = msg.index(prefix) + len(prefix)
                end = msg.find(" ", start)
                end = end if end != -1 else msg.find(",", start)
                end = end if end != -1 else len(msg)
                return msg[start:end].strip()
        return ""

    @staticmethod
    def _extract_event_type_from_alert(alert: dict) -> str:
        """从alert message中提取event_type。"""
        msg = alert.get("message", "")
        # 格式: "...({event_type})..."
        if "(" in msg and ")" in msg:
            start = msg.index("(") + 1
            end = msg.index(")", start)
            return msg[start:end]
        return ""

    @staticmethod
    def _extract_age_from_message(msg: str) -> float | None:
        """从message中提取秒数，如 'for 350s' 或 'after 120s'。"""
        import re
        m = re.search(r"(\d+)s", msg)
        if m:
            return float(m.group(1))
        return None

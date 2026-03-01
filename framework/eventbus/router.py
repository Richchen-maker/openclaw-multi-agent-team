"""
Event routing table: event_type → target_team + target_mode.

Hardcoded defaults, overridable via config.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_ROUTES: dict[str, dict[str, str]] = {
    "DATA_GAP":           {"target_team": "data-collection-team", "target_mode": "A"},
    "CRAWL_BLOCKED":      {"target_team": "arc-team",             "target_mode": "C"},
    "CRAWL_STRATEGY":     {"target_team": "arc-team",             "target_mode": "B"},
    "DEFENSE_REPORT":     {"target_team": "data-collection-team", "target_mode": "A"},
    "DATA_READY":         {"target_team": "ecommerce-team",       "target_mode": "A"},
    "ANOMALY":            {"target_team": "data-collection-team", "target_mode": "B"},
    "MARKET_SIGNAL":      {"target_team": "ecommerce-team",       "target_mode": "A"},
    "SECURITY_INCIDENT":  {"target_team": "arc-team",             "target_mode": "C"},
}


class Router:
    """Route events to target teams based on event_type."""

    def __init__(self, routes: dict[str, dict[str, str]] | None = None, workspace_dir: Path | None = None) -> None:
        if routes is not None:
            self.routes = routes
        elif workspace_dir is not None:
            # 尝试动态发现
            from .registry import Registry
            reg = Registry(workspace_dir)
            count = reg.scan()
            if count > 0:
                self.routes = reg.get_all_routes()
                logger.info("Dynamic routes loaded from %d teams", count)
            else:
                self.routes = dict(DEFAULT_ROUTES)
        else:
            self.routes = dict(DEFAULT_ROUTES)

    def resolve(self, event_type: str) -> dict[str, str] | None:
        """Resolve event_type to route info.

        Returns:
            Dict with target_team and target_mode, or None if no route.
        """
        route = self.routes.get(event_type)
        if route is None:
            logger.warning("No route for event_type=%s", event_type)
        return route

    def add_route(self, event_type: str, target_team: str, target_mode: str) -> None:
        """Register a new route."""
        self.routes[event_type] = {"target_team": target_team, "target_mode": target_mode}

    def list_routes(self) -> dict[str, dict[str, str]]:
        """Return all registered routes."""
        return dict(self.routes)

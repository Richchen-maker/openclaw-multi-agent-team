"""
EventBus - Event-driven inter-team communication runtime.

Scans pending events, routes them to target teams, and dispatches execution.
"""

from .event import Event
from .bus import EventBus
from .router import Router, DEFAULT_ROUTES
from .config import load_config, DEFAULT_CONFIG

__all__ = ["Event", "EventBus", "Router", "DEFAULT_ROUTES", "load_config", "DEFAULT_CONFIG"]

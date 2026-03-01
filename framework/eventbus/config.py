"""
Configuration management for EventBus.

Loads defaults, merges with eventbus.yaml if present.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: dict[str, Any] = {
    "workspace_dir": ".",
    "poll_interval": 60,          # 轮询间隔（秒）
    "max_chain_depth": 5,         # 事件链最大深度
    "dedup_window": 3600,         # 去重窗口（秒）
    "processing_timeout": 1800,   # processing超时（秒）
    "resolved_retention": 7,      # resolved事件保留天数
    "dispatch_model": None,        # sub-agent模型override，None=默认
    "dispatch_timeout": 300,       # sub-agent超时秒数
    "dispatch_mode": "default",    # "default" (print) 或 "live" (spawn)
    "daemon_pid_file": "eventbus.pid",  # PID文件名（相对于events/.watchdog/）
    "bus_mode": "cron",            # "cron" (skip BUS_DOWN check) 或 "daemon"
}


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load config from eventbus.yaml, falling back to defaults.

    Args:
        config_path: Explicit path to config file. If None, searches cwd.

    Returns:
        Merged configuration dict.
    """
    config = dict(DEFAULT_CONFIG)

    if config_path is None:
        config_path = Path("eventbus.yaml")

    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                overrides = yaml.safe_load(f) or {}
            config.update(overrides)
            logger.info("Loaded config from %s", config_path)
        except Exception as e:
            logger.warning("Failed to load %s: %s, using defaults", config_path, e)
    else:
        logger.debug("No config file at %s, using defaults", config_path)

    return config

"""Configuration package — lazy access to settings, logging, and Redis helpers."""
from __future__ import annotations

from importlib import import_module
from typing import Any


__all__ = [
    "get_settings",
    "reset_settings_cache",
    "settings",
    "reset_redis_client",
    "setup_logging",
    "check_redis_connection",
    "delete_cache",
    "get_cache",
    "get_redis_client",
    "set_cache",
]


def __getattr__(name: str) -> Any:
    if name in {"get_settings", "reset_settings_cache", "settings"}:
        return getattr(import_module("nova.config.settings"), name)
    if name == "setup_logging":
        return import_module("nova.config.logging").setup_logging
    if name in {
        "check_redis_connection",
        "delete_cache",
        "get_cache",
        "get_redis_client",
        "reset_redis_client",
        "set_cache",
    }:
        return getattr(import_module("nova.config.redis"), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

"""Configuration package — settings, logging, constants."""

from nova.config.settings import settings
from nova.config.logging import setup_logging

__all__ = ["settings", "setup_logging"]

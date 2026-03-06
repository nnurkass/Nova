"""
Logging configuration for the Nova application.

Sets up structured logging with configurable levels and LangSmith
tracing integration.

Implemented in Step 1.2.
"""

import logging
import os

from nova.config.settings import get_settings


def setup_logging(level: str | None = None) -> logging.Logger:
    """Configure root logger and optionally enable LangSmith tracing.

    Args:
        level: Override log level (e.g. "DEBUG"). Falls back to settings.log_level.

    Returns:
        Configured root logger.
    """

    settings = get_settings()
    resolved_level = (level or settings.log_level).upper()

    logging.basicConfig(
        level=resolved_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )
    # Explicitly set root level so this is effective even when handlers already exist
    logging.getLogger().setLevel(resolved_level)

    # Silence noisy third-party loggers
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    # Enable LangSmith tracing when configured
    if settings.langchain_tracing_v2 and settings.langsmith_api_key is not None:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
        os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    else:
        for key in ("LANGCHAIN_TRACING_V2", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
            os.environ.pop(key, None)

    return logging.getLogger()

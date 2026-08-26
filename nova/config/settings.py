"""
Centralized configuration via Pydantic BaseSettings.

Settings are loaded lazily so imports do not depend on environment readiness.
The default .env path is resolved relative to the project root, not the cwd.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Anthropic LLM ---
    anthropic_api_key: SecretStr = SecretStr("mock-anthropic-key")

    # --- OpenRouter LLM ---
    openrouter_api_key: SecretStr | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta/muse-glimmer-30b"

    # --- OpenAI LLM ---
    openai_api_key: SecretStr | None = None

    # --- Goszakup.gov.kz API ---
    goszakup_token: SecretStr
    goszakup_graphql_url: str = "https://ows.goszakup.gov.kz/v3/graphql"

    # --- PostgreSQL ---
    database_url: str

    # --- Redis ---
    redis_url: str = "redis://localhost:6379/0"

    # --- LangSmith (tracing & monitoring) ---
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str = "nova-construction-ai"
    langchain_tracing_v2: bool = False

    # --- ABC Smetnie Resheniya ---
    abc_export_path: str = "/data/abc/exports"
    abc_import_path: str = "/data/abc/imports"

    # --- Application ---
    app_env: str = "development"
    log_level: str = "INFO"

    # --- FastAPI ---
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()


def reset_settings_cache() -> None:
    """Clear the cached settings instance."""
    get_settings.cache_clear()


def __getattr__(name: str) -> Any:
    if name == "settings":
        return get_settings()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "DEFAULT_ENV_FILE",
    "Settings",
    "get_settings",
    "reset_settings_cache",
    "settings",
]

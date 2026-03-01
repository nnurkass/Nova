"""
Centralized configuration via Pydantic BaseSettings.

Settings class reads all configuration from environment variables
(or .env file). Provides a single `settings` singleton for the entire app.

Implemented in Step 1.2.
"""

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Anthropic LLM ---
    anthropic_api_key: SecretStr

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


settings = Settings()

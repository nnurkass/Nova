"""Unit tests for nova/config/settings.py and nova/config/logging.py."""

import logging
import os

import pytest
from pydantic import SecretStr

from nova.config.settings import Settings
from nova.config.logging import setup_logging


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_ENV = {
    "ANTHROPIC_API_KEY": "sk-ant-test",
    "DATABASE_URL": "postgresql://user:pass@localhost:5432/testdb",
}


@pytest.fixture()
def minimal_env(monkeypatch):
    """Set minimum required env vars and disable .env file loading."""
    for key, val in MINIMAL_ENV.items():
        monkeypatch.setenv(key, val)


def make_settings(monkeypatch, **overrides) -> Settings:
    """Set env vars and return a fresh Settings instance (no .env file)."""
    for key, val in {**MINIMAL_ENV, **overrides}.items():
        monkeypatch.setenv(key, val)
    return Settings(_env_file=None)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Settings tests
# ---------------------------------------------------------------------------


class TestSettings:
    def test_minimal_required_fields(self, monkeypatch):
        s = make_settings(monkeypatch)
        assert isinstance(s.anthropic_api_key, SecretStr)
        assert s.anthropic_api_key.get_secret_value() == "sk-ant-test"
        assert s.database_url == "postgresql://user:pass@localhost:5432/testdb"

    def test_defaults(self, monkeypatch):
        s = make_settings(monkeypatch)
        assert s.goszakup_base_url == "https://goszakup.gov.kz"
        assert s.goszakup_request_delay == 1.5
        assert s.goszakup_timeout == 30
        assert s.redis_url == "redis://localhost:6379/0"
        assert s.langsmith_api_key is None
        assert s.langsmith_project == "nova-construction-ai"
        assert s.langchain_tracing_v2 is False
        assert s.abc_export_path == "/data/abc/exports"
        assert s.abc_import_path == "/data/abc/imports"
        assert s.app_env == "development"
        assert s.log_level == "INFO"
        assert s.api_host == "0.0.0.0"
        assert s.api_port == 8000

    def test_is_production_false_for_development(self, monkeypatch):
        s = make_settings(monkeypatch, APP_ENV="development")
        assert s.is_production is False

    def test_is_production_true_for_production(self, monkeypatch):
        s = make_settings(monkeypatch, APP_ENV="production")
        assert s.is_production is True

    def test_custom_api_port(self, monkeypatch):
        s = make_settings(monkeypatch, API_PORT="9000")
        assert s.api_port == 9000

    def test_langsmith_optional_key(self, monkeypatch):
        s = make_settings(monkeypatch, LANGSMITH_API_KEY="ls-key-abc")
        assert s.langsmith_api_key is not None
        assert s.langsmith_api_key.get_secret_value() == "ls-key-abc"

    def test_langchain_tracing_bool_parsing(self, monkeypatch):
        s = make_settings(monkeypatch, LANGCHAIN_TRACING_V2="true")
        assert s.langchain_tracing_v2 is True

        s2 = make_settings(monkeypatch, LANGCHAIN_TRACING_V2="false")
        assert s2.langchain_tracing_v2 is False


# ---------------------------------------------------------------------------
# Logging tests
# ---------------------------------------------------------------------------


class TestSetupLogging:
    def _make_settings(self, monkeypatch, **kwargs):
        return make_settings(monkeypatch, **kwargs)

    def test_setup_logging_returns_root_logger(self, monkeypatch):
        fake = self._make_settings(monkeypatch)
        monkeypatch.setattr("nova.config.logging.settings", fake)
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)

    def test_setup_logging_level_override(self, monkeypatch):
        fake = self._make_settings(monkeypatch)
        monkeypatch.setattr("nova.config.logging.settings", fake)
        setup_logging(level="DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    def test_langsmith_env_vars_set_when_tracing_enabled(self, monkeypatch):
        fake = self._make_settings(
            monkeypatch,
            LANGCHAIN_TRACING_V2="true",
            LANGSMITH_API_KEY="ls-secret",
            LANGSMITH_PROJECT="my-project",
        )
        monkeypatch.setattr("nova.config.logging.settings", fake)
        for key in ("LANGCHAIN_TRACING_V2", "LANGSMITH_API_KEY", "LANGSMITH_PROJECT"):
            monkeypatch.delenv(key, raising=False)

        setup_logging()

        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"
        assert os.environ.get("LANGSMITH_API_KEY") == "ls-secret"
        assert os.environ.get("LANGSMITH_PROJECT") == "my-project"

    def test_langsmith_env_vars_not_set_when_tracing_disabled(self, monkeypatch):
        fake = self._make_settings(monkeypatch, LANGCHAIN_TRACING_V2="false")
        monkeypatch.setattr("nova.config.logging.settings", fake)
        monkeypatch.delenv("LANGCHAIN_TRACING_V2", raising=False)
        monkeypatch.delenv("LANGSMITH_API_KEY", raising=False)

        setup_logging()

        assert os.environ.get("LANGCHAIN_TRACING_V2") != "true"

    def test_noisy_loggers_silenced(self, monkeypatch):
        fake = self._make_settings(monkeypatch)
        monkeypatch.setattr("nova.config.logging.settings", fake)
        setup_logging()
        assert logging.getLogger("httpx").level == logging.WARNING
        assert logging.getLogger("httpcore").level == logging.WARNING

"""Pytest configuration and shared fixtures."""
from __future__ import annotations

import os

import pytest


os.environ.setdefault("ANTHROPIC_API_KEY", "sk-ant-test")
os.environ.setdefault("GOSZAKUP_TOKEN", "goszakup-test")
os.environ.setdefault("DATABASE_URL", "sqlite:///./nova_test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")


@pytest.fixture()
def initial_construction_state() -> dict[str, object]:
    return {
        "task": "Найти тендер на строительство школы",
        "tenders": [],
        "selected_tender": None,
        "work_list": [],
        "materials_list": [],
        "stock_check": {},
        "purchase_orders": [],
        "current_agent": "",
        "messages": [],
        "errors": [],
        "metadata": {},
    }

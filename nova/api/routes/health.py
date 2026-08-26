"""
Health check route for system component diagnostics.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from nova.config import get_settings
from nova.config.redis import check_redis_connection
from nova.db.database import get_db
from nova.integrations.goszakup.client import GoszakupClient

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Check overall system health and connectivity to external services."""
    settings = get_settings()

    # 1. Database check
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    # 2. Redis check
    redis_ok = False
    try:
        redis_ok = check_redis_connection()
    except Exception:
        redis_ok = False

    # 3. Goszakup client mode
    client = GoszakupClient()
    goszakup_mode = "mock_fallback" if client.is_mock_mode else "live_api"

    # 4. LLM provider mode
    api_key = (
        settings.anthropic_api_key.get_secret_value()
        if hasattr(settings.anthropic_api_key, "get_secret_value")
        else str(settings.anthropic_api_key)
    )
    llm_mode = "mock_fallback" if (not api_key or "mock" in api_key or "test" in api_key) else "live_claude"

    overall_status = "ok" if db_ok else "degraded"

    return {
        "status": overall_status,
        "app_env": settings.app_env,
        "components": {
            "database": "connected" if db_ok else "disconnected",
            "redis": "connected" if redis_ok else "unavailable (fallback to memory)",
            "goszakup_api": goszakup_mode,
            "llm_provider": llm_mode,
        },
    }

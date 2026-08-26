"""
FastAPI application entry point for the Nova multi-agent construction system.
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nova.api.routes.health import router as health_router
from nova.api.routes.tasks import router as tasks_router
from nova.config import get_settings
from nova.config.logging import setup_logging
from nova.db.database import _get_app_engine
from nova.db.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifespan events."""
    setup_logging()
    # Initialize DB tables for development/testing if not created via Alembic
    engine = _get_app_engine()
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Nova Construction AI API",
    description="Multi-Agent AI system for construction procurement and tender execution in Kazakhstan.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(tasks_router)


@app.get("/", tags=["Root"])
def root_info() -> dict[str, str]:
    return {
        "service": "Nova Multi-Agent Construction AI",
        "status": "online",
        "docs_url": "/docs",
    }


__all__ = ["app"]

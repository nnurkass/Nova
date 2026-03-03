"""SQLAlchemy database engine and session configuration. Implemented in Step 1.4."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def get_engine(url: str, **kwargs) -> Engine:
    """Create an Engine for the given URL. SQLite gets check_same_thread=False."""
    connect_args: dict = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, **kwargs)


@contextmanager
def get_session(eng: Engine) -> Generator[Session, None, None]:
    """Context manager yielding an open Session. Caller handles commit/rollback."""
    session = Session(eng)
    try:
        yield session
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Module-level lazy singletons — used by FastAPI routes and Alembic
# ---------------------------------------------------------------------------

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def _get_app_engine() -> Engine:
    global _engine
    if _engine is None:
        from nova.config.settings import settings
        _engine = get_engine(settings.database_url)
    return _engine


def _get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=_get_app_engine(), expire_on_commit=False)
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: yields a request-scoped Session with auto commit/rollback."""
    factory = _get_session_factory()
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

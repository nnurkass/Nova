"""SQLAlchemy database engine and session configuration. Implemented in Step 1.4."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from nova.config.settings import get_settings


def get_engine(url: str, **kwargs) -> Engine:
    """Create an Engine for the given URL. SQLite gets check_same_thread=False and timeout."""
    connect_args: dict = dict(kwargs.pop("connect_args", {}))
    if url.startswith("sqlite"):
        connect_args.setdefault("check_same_thread", False)
        connect_args.setdefault("timeout", 30.0)
    engine = create_engine(url, connect_args=connect_args, **kwargs)
    if url.startswith("sqlite"):
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
    return engine


@contextmanager
def get_session(eng: Engine) -> Generator[Session, None, None]:
    """Context manager yielding an open Session. Caller handles commit."""
    session = Session(eng)
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# Module-level lazy singletons — used by FastAPI routes and Alembic
# ---------------------------------------------------------------------------

_engines: dict[str, Engine] = {}
_session_factories: dict[str, sessionmaker[Session]] = {}


def _get_app_engine() -> Engine:
    database_url = get_settings().database_url
    engine = _engines.get(database_url)
    if engine is None:
        engine = get_engine(database_url)
        _engines[database_url] = engine
    return engine


def _get_session_factory() -> sessionmaker[Session]:
    database_url = get_settings().database_url
    factory = _session_factories.get(database_url)
    if factory is None:
        factory = sessionmaker(bind=_get_app_engine(), expire_on_commit=False)
        _session_factories[database_url] = factory
    return factory


def reset_db_singletons() -> None:
    """Dispose cached engines and clear cached session factories."""
    for engine in _engines.values():
        engine.dispose()
    _engines.clear()
    _session_factories.clear()


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

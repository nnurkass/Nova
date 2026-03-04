"""Unit tests for Step 1.4 — database models and session management.

Uses an in-memory SQLite database. No live PostgreSQL connection required.
"""
import uuid
import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from nova.db.models import Base, Task, TenderRecord, AgentLog
from nova.db.database import get_engine, get_session


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def session(engine):
    with Session(engine) as s:
        yield s
        s.rollback()


class TestModelsExist:
    def test_task_table_exists(self, engine):
        assert "tasks" in inspect(engine).get_table_names()

    def test_tender_record_table_exists(self, engine):
        assert "tender_records" in inspect(engine).get_table_names()

    def test_agent_log_table_exists(self, engine):
        assert "agent_logs" in inspect(engine).get_table_names()

    def test_task_columns(self, engine):
        cols = {c["name"] for c in inspect(engine).get_columns("tasks")}
        assert {"id", "status", "input_text", "output_json", "created_at", "updated_at"}.issubset(cols)

    def test_tender_record_columns(self, engine):
        cols = {c["name"] for c in inspect(engine).get_columns("tender_records")}
        assert {"id", "task_id", "tender_id", "tender_number", "tender_name", "created_at"}.issubset(cols)

    def test_agent_log_columns(self, engine):
        cols = {c["name"] for c in inspect(engine).get_columns("agent_logs")}
        assert {"id", "task_id", "agent_name", "status", "input_json", "output_json",
                "started_at", "finished_at", "error_message"}.issubset(cols)


class TestTaskCRUD:
    def test_create_task(self, session):
        task = Task(status="pending", input_text="Найти тендер на строительство")
        session.add(task)
        session.flush()
        assert task.id is not None
        assert isinstance(task.id, uuid.UUID)
        assert task.output_json is None
        assert task.created_at is not None

    def test_update_task_status(self, session):
        task = Task(status="pending", input_text="тест")
        session.add(task)
        session.flush()
        assert task.updated_at is not None
        task.status = "running"
        session.flush()
        fetched = session.get(Task, task.id)
        assert fetched.status == "running"
        assert fetched.updated_at is not None

    def test_task_with_output(self, session):
        task = Task(status="completed", input_text="тест", output_json={"result": "ok"})
        session.add(task)
        session.flush()
        assert session.get(Task, task.id).output_json == {"result": "ok"}


class TestTenderRecordCRUD:
    def test_create_tender_record(self, session):
        task = Task(status="running", input_text="тест")
        session.add(task)
        session.flush()
        record = TenderRecord(
            task_id=task.id,
            tender_id="12345",
            tender_number="АНО-2026-001",
            tender_name="Строительство дороги",
        )
        session.add(record)
        session.flush()
        assert record.id is not None
        assert record.task_id == task.id

    def test_multiple_tender_records_per_task(self, session):
        task = Task(status="running", input_text="тест")
        session.add(task)
        session.flush()
        for i in range(3):
            session.add(TenderRecord(task_id=task.id, tender_id=str(i),
                                     tender_number=f"АНО-{i}", tender_name=f"Тендер {i}"))
        session.flush()
        records = session.scalars(
            select(TenderRecord).where(TenderRecord.task_id == task.id)
        ).all()
        assert len(records) == 3


class TestAgentLogCRUD:
    def test_create_agent_log(self, session):
        task = Task(status="running", input_text="тест")
        session.add(task)
        session.flush()
        log = AgentLog(
            task_id=task.id,
            agent_name="procurement",
            status="success",
            input_json={"query": "тендер"},
            output_json={"tenders": []},
        )
        session.add(log)
        session.flush()
        assert log.id is not None
        assert log.agent_name == "procurement"

    def test_agent_log_with_error(self, session):
        task = Task(status="failed", input_text="тест")
        session.add(task)
        session.flush()
        log = AgentLog(task_id=task.id, agent_name="pto", status="error",
                       error_message="Timeout after 180s")
        session.add(log)
        session.flush()
        fetched = session.get(AgentLog, log.id)
        assert fetched.status == "error"
        assert fetched.error_message == "Timeout after 180s"


class TestDatabaseHelpers:
    def test_get_engine_returns_engine(self):
        from sqlalchemy.engine import Engine
        eng = get_engine("sqlite:///:memory:")
        assert isinstance(eng, Engine)
        eng.dispose()

    def test_get_session_is_context_manager(self):
        from sqlalchemy import text
        eng = get_engine("sqlite:///:memory:")
        Base.metadata.create_all(eng)
        with get_session(eng) as s:
            assert isinstance(s, Session)
            s.execute(text("SELECT 1"))
        eng.dispose()

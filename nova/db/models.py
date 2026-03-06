"""SQLAlchemy ORM models for the Nova database. Implemented in Step 1.4."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, validates
from sqlalchemy.types import JSON

from nova.statuses import AGENT_LOG_STATUS_VALUES, TASK_STATUS_VALUES, AgentLogStatusEnum, TaskStatusEnum


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validate_status(value: str | TaskStatusEnum | AgentLogStatusEnum, allowed: tuple[str, ...]) -> str:
    normalized = value.value if hasattr(value, "value") else value
    if normalized not in allowed:
        allowed_values = ", ".join(allowed)
        raise ValueError(f"status must be one of: {allowed_values}")
    return normalized


class Base(DeclarativeBase):
    pass


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed')",
            name="ck_tasks_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    input_text: Mapped[str] = mapped_column(Text, nullable=False)
    output_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now
    )

    tender_records: Mapped[list[TenderRecord]] = relationship(back_populates="task", cascade="all, delete-orphan")
    agent_logs: Mapped[list[AgentLog]] = relationship(back_populates="task", cascade="all, delete-orphan")

    @validates("status")
    def validate_status(self, _: str, value: str | TaskStatusEnum) -> str:
        return _validate_status(value, TASK_STATUS_VALUES)

    def __repr__(self) -> str:
        return f"<Task id={self.id} status={self.status!r}>"


class TenderRecord(Base):
    __tablename__ = "tender_records"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    tender_id: Mapped[str] = mapped_column(String(100), nullable=False)
    tender_number: Mapped[str] = mapped_column(String(100), nullable=False)
    tender_name: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[Optional[float]] = mapped_column(nullable=True, default=None)
    raw_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)

    task: Mapped[Task] = relationship(back_populates="tender_records")

    def __repr__(self) -> str:
        return f"<TenderRecord id={self.id} number={self.tender_number!r}>"


class AgentLog(Base):
    __tablename__ = "agent_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'success', 'error')",
            name="ck_agent_logs_status_valid",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    task_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    input_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True, default=None
    )
    output_json: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=True, default=None
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default=None)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, default=None)

    task: Mapped[Task] = relationship(back_populates="agent_logs")

    @validates("status")
    def validate_status(self, _: str, value: str | AgentLogStatusEnum) -> str:
        return _validate_status(value, AGENT_LOG_STATUS_VALUES)

    def __repr__(self) -> str:
        return f"<AgentLog id={self.id} agent={self.agent_name!r} status={self.status!r}>"

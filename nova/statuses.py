"""Shared status enums used by API schemas and persistence models."""
from __future__ import annotations

from enum import Enum


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentLogStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


TASK_STATUS_VALUES = tuple(status.value for status in TaskStatusEnum)
AGENT_LOG_STATUS_VALUES = tuple(status.value for status in AgentLogStatusEnum)

"""
Pydantic schemas for FastAPI request/response models.

Schemas:
- TaskRequest: input for creating a new task
- TaskResponse: response with task ID and status
- TaskStatus: current state of a running task
- AgentReport: final report from agent pipeline

Implemented in Step 1.3.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatusEnum(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TaskRequest(BaseModel):
    task_description: str
    region: Optional[str] = None
    work_type: Optional[str] = None
    budget_max: Optional[float] = None


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatusEnum
    created_at: datetime
    message: str = ""


class TaskStatus(BaseModel):
    task_id: str
    status: TaskStatusEnum
    current_agent: Optional[str] = None
    progress_pct: int = Field(0, ge=0, le=100)
    result: Optional[dict[str, Any]] = None
    errors: list[str] = Field(default_factory=list)
    updated_at: datetime


class AgentReport(BaseModel):
    task_id: str
    tenders_found: int = 0
    selected_tender: Optional[dict[str, Any]] = None
    resource_statement: Optional[dict[str, Any]] = None
    purchase_orders: list[dict[str, Any]] = Field(default_factory=list)
    total_budget_estimate: Optional[float] = None
    execution_time_seconds: Optional[float] = None
    created_at: datetime

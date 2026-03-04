"""Pydantic schemas for FastAPI request/response models."""
from __future__ import annotations
from typing import Optional, Any
from enum import Enum
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskRequest(BaseModel):
    task: str
    region: Optional[str] = None
    budget_max: Optional[float] = None


class TaskResponse(BaseModel):
    task_id: UUID
    status: TaskStatusEnum
    created_at: datetime


class TaskStatus(BaseModel):
    task_id: UUID
    status: TaskStatusEnum
    progress: float = 0.0
    current_agent: Optional[str] = None
    message: Optional[str] = None
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class AgentReport(BaseModel):
    task_id: UUID
    task: str
    selected_tender: Optional[dict[str, Any]] = None
    resource_statement: Optional[dict[str, Any]] = None
    stock_summary: Optional[dict[str, Any]] = None
    purchase_orders: list[dict[str, Any]] = []
    total_cost_estimate: Optional[float] = None
    recommendations: str
    created_at: datetime

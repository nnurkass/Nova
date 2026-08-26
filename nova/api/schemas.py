"""Pydantic schemas for FastAPI request/response models."""
from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from nova.statuses import TaskStatusEnum


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
    purchase_orders: list[dict[str, Any]] = Field(default_factory=list)
    total_cost_estimate: Optional[float] = None
    recommendations: str
    created_at: datetime


class ChatMessageSchema(BaseModel):
    role: str = "user"  # "user" | "assistant" | "system"
    content: str
    sender: Optional[str] = None  # "user" | "coo" | "procurement" | "pto" | "supply"
    timestamp: Optional[str] = None
    thought: Optional[str] = None
    artifacts: Optional[dict[str, Any]] = None


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessageSchema] = Field(default_factory=list)
    task_id: Optional[UUID] = None
    current_state: Optional[dict[str, Any]] = None


class ChatResponse(BaseModel):
    response: str
    sender: str = "coo"
    sender_title: str = "Операционный директор (COO)"
    thought: Optional[str] = None
    state: Optional[dict[str, Any]] = None
    suggestions: list[str] = Field(default_factory=list)


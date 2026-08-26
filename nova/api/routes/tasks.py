"""
API endpoints for managing and executing construction procurement tasks.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from nova.api.schemas import AgentReport, TaskRequest, TaskResponse, TaskStatus
from nova.db.database import get_db
from nova.db.models import AgentLog, Base, Task, TenderRecord
from nova.graph.main_graph import run_pipeline
from nova.statuses import AgentLogStatusEnum, TaskStatusEnum

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


@router.post("", response_model=TaskResponse, status_code=201)
def create_and_run_task(
    payload: TaskRequest,
    db: Session = Depends(get_db),
) -> TaskResponse:
    """Create a new procurement task, run the multi-agent pipeline, and save records."""
    # Ensure tables exist in SQLite / development environments
    Base.metadata.create_all(bind=db.get_bind())

    task_id = uuid.uuid4()
    now = _now()

    db_task = Task(
        id=task_id,
        status=TaskStatusEnum.RUNNING.value,
        input_text=payload.task,
        created_at=now,
        updated_at=now,
    )
    db.add(db_task)
    db.flush()

    try:
        final_state = run_pipeline(payload.task)

        # Record agent logs
        for agent_name in ["coo", "procurement", "pto", "supply"]:
            agent_log = AgentLog(
                id=uuid.uuid4(),
                task_id=task_id,
                agent_name=agent_name,
                status=AgentLogStatusEnum.SUCCESS.value,
                started_at=now,
                finished_at=_now(),
            )
            db.add(agent_log)

        # Record tender if found
        selected_tender = final_state.get("selected_tender")
        if selected_tender:
            tender_rec = TenderRecord(
                id=uuid.uuid4(),
                task_id=task_id,
                tender_id=str(selected_tender.id),
                tender_number=selected_tender.number,
                tender_name=selected_tender.name_ru,
                score=85.0,
                raw_json=selected_tender.model_dump(mode="json"),
                created_at=_now(),
            )
            db.add(tender_rec)

        # Serialize state output
        output_payload: dict[str, Any] = {
            "task": payload.task,
            "selected_tender": selected_tender.model_dump(mode="json") if selected_tender else None,
            "work_list": [w.model_dump(mode="json") for w in final_state.get("work_list", [])],
            "materials_list": [m.model_dump(mode="json") for m in final_state.get("materials_list", [])],
            "stock_check": final_state.get("stock_check", {}),
            "purchase_orders": final_state.get("purchase_orders", []),
            "executive_summary": final_state.get("metadata", {}).get("final_report", ""),
            "visited_nodes": final_state.get("metadata", {}).get("visited_nodes", []),
        }

        db_task.status = TaskStatusEnum.COMPLETED.value
        db_task.output_json = output_payload
        db_task.updated_at = _now()
        db.flush()

        return TaskResponse(
            task_id=task_id,
            status=TaskStatusEnum.COMPLETED,
            created_at=db_task.created_at,
        )
    except Exception as exc:
        logger.error("Task execution failed: %s", exc)
        db_task.status = TaskStatusEnum.FAILED.value
        db_task.output_json = {"error": str(exc)}
        db_task.updated_at = _now()
        db.flush()
        raise HTTPException(status_code=500, detail=f"Task execution failed: {exc}")


@router.get("/{task_id}", response_model=TaskStatus)
def get_task_status(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> TaskStatus:
    """Retrieve current task status and result."""
    stmt = select(Task).where(Task.id == task_id)
    db_task = db.scalar(stmt)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    is_done = db_task.status in {TaskStatusEnum.COMPLETED.value, TaskStatusEnum.FAILED.value}

    return TaskStatus(
        task_id=db_task.id,
        status=TaskStatusEnum(db_task.status),
        progress=1.0 if is_done else 0.5,
        current_agent="coo" if is_done else "running",
        result=db_task.output_json,
        error=db_task.output_json.get("error") if (db_task.output_json and db_task.status == "failed") else None,
        created_at=db_task.created_at,
        updated_at=db_task.updated_at,
    )


@router.get("", response_model=list[TaskStatus])
def list_tasks(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[TaskStatus]:
    """List recent procurement tasks."""
    stmt = select(Task).order_by(Task.created_at.desc()).limit(limit)
    tasks = db.scalars(stmt).all()

    return [
        TaskStatus(
            task_id=t.id,
            status=TaskStatusEnum(t.status),
            progress=1.0 if t.status in {"completed", "failed"} else 0.5,
            current_agent="coo" if t.status == "completed" else t.status,
            result=t.output_json,
            error=t.output_json.get("error") if (t.output_json and t.status == "failed") else None,
            created_at=t.created_at,
            updated_at=t.updated_at,
        )
        for t in tasks
    ]


@router.get("/{task_id}/report", response_model=AgentReport)
def get_task_report(
    task_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> AgentReport:
    """Get structured AgentReport for the given task."""
    stmt = select(Task).where(Task.id == task_id)
    db_task = db.scalar(stmt)
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    output = db_task.output_json or {}
    return AgentReport(
        task_id=db_task.id,
        task=db_task.input_text,
        selected_tender=output.get("selected_tender"),
        resource_statement={"materials": output.get("materials_list", []), "works": output.get("work_list", [])},
        stock_summary=output.get("stock_check", {}).get("summary"),
        purchase_orders=output.get("purchase_orders", []),
        total_cost_estimate=output.get("stock_check", {}).get("summary", {}).get("total_required_cost"),
        recommendations=output.get("executive_summary", "Рекомендовано к участию"),
        created_at=db_task.created_at,
    )

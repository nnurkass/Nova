"""add status constraints

Revision ID: 76fdd0b0f0a8
Revises: e0f0d7fe3562
Create Date: 2026-03-06 20:30:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "76fdd0b0f0a8"
down_revision: Union[str, None] = "e0f0d7fe3562"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_tasks_status_valid",
        "tasks",
        "status IN ('pending', 'running', 'completed', 'failed')",
    )
    op.create_check_constraint(
        "ck_agent_logs_status_valid",
        "agent_logs",
        "status IN ('pending', 'running', 'success', 'error')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_agent_logs_status_valid", "agent_logs", type_="check")
    op.drop_constraint("ck_tasks_status_valid", "tasks", type_="check")

"""Milestone 5 — offline sync: note client_operation_id for idempotency.

Revision ID: 20261127_0003
Revises: 20261126_0002
Create Date: 2026-11-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261127_0003"
down_revision: Union[str, None] = "20261126_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "job_activities",
        sa.Column(
            "client_operation_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "job_activities",
        sa.Column(
            "client_occurred_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_job_activities_client_operation_id",
        "job_activities",
        ["client_operation_id"],
    )
    # Idempotent note retries: unique per org when client_operation_id is set
    op.create_index(
        "uq_job_activities_org_client_operation",
        "job_activities",
        ["organization_id", "client_operation_id"],
        unique=True,
        postgresql_where=sa.text("client_operation_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_job_activities_org_client_operation",
        table_name="job_activities",
    )
    op.drop_index(
        "ix_job_activities_client_operation_id",
        table_name="job_activities",
    )
    op.drop_column("job_activities", "client_occurred_at")
    op.drop_column("job_activities", "client_operation_id")

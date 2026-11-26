"""Milestone 2 — scheduled windows for overlap detection.

Revision ID: 20261126_0002
Revises: 20261126_0001
Create Date: 2026-11-26
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "20261126_0002"
down_revision: Union[str, None] = "20261126_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "work_orders",
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "work_orders",
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_work_orders_scheduled_start", "work_orders", ["scheduled_start"]
    )


def downgrade() -> None:
    op.drop_index("ix_work_orders_scheduled_start", table_name="work_orders")
    op.drop_column("work_orders", "scheduled_end")
    op.drop_column("work_orders", "scheduled_start")

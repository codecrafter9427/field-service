"""Milestone 6 — customer_portal_links for job-status portal.

Revision ID: 20261127_0004
Revises: 20261127_0003
Create Date: 2026-11-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261127_0004"
down_revision: Union[str, None] = "20261127_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customer_portal_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "work_order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("work_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_customer_portal_links_organization_id",
        "customer_portal_links",
        ["organization_id"],
    )
    op.create_index(
        "ix_customer_portal_links_work_order_id",
        "customer_portal_links",
        ["work_order_id"],
    )
    op.create_index(
        "ix_customer_portal_links_token_hash",
        "customer_portal_links",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_customer_portal_links_token_hash", table_name="customer_portal_links")
    op.drop_index(
        "ix_customer_portal_links_work_order_id", table_name="customer_portal_links"
    )
    op.drop_index(
        "ix_customer_portal_links_organization_id", table_name="customer_portal_links"
    )
    op.drop_table("customer_portal_links")

"""Customer portal link and redacted public job-status schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class PortalLinkCreate(BaseModel):
    expire_hours: int | None = Field(
        default=None,
        ge=1,
        le=24 * 90,
        description="Optional TTL override; defaults to PORTAL_LINK_EXPIRE_HOURS",
    )


class PortalLinkCreated(BaseModel):
    id: UUID
    work_order_id: UUID
    url_path: str
    raw_token: str
    expires_at: datetime
    created_at: datetime


class PortalLinkOut(BaseModel):
    id: UUID
    work_order_id: UUID
    expires_at: datetime
    revoked_at: datetime | None = None
    created_by_id: UUID | None = None
    created_at: datetime
    last_accessed_at: datetime | None = None
    is_active: bool


class PortalPartPublic(BaseModel):
    part_name: str
    quantity: Decimal


class ChecklistProgressPublic(BaseModel):
    completed: int
    total: int


class CustomerJobStatusOut(BaseModel):
    """Allowlisted customer-facing payload — no notes, rates, or tech private data."""

    work_order_id: UUID
    title: str
    status: str
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    customer_name: str | None = None
    location_label: str | None = None
    asset_name: str | None = None
    service_summary: str | None = None
    checklist_progress: ChecklistProgressPublic | None = None
    parts: list[PortalPartPublic] = Field(default_factory=list)
    acknowledgement_recorded: bool = False
    acknowledged_at: datetime | None = None
    generated_at: datetime
    link_expires_at: datetime

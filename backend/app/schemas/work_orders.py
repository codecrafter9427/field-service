"""Work order, assignment, notes, checklist, and time-entry schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class WorkOrderCreate(BaseModel):
    customer_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    service_location_id: UUID | None = None
    asset_id: UUID | None = None
    status: str = "draft"
    priority: str = "normal"
    due_at: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    skill_required: str | None = Field(default=None, max_length=100)
    estimate_amount: Decimal | None = None
    labor_rate: Decimal | None = None
    technician_id: UUID | None = None


class WorkOrderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    customer_id: UUID | None = None
    service_location_id: UUID | None = None
    asset_id: UUID | None = None
    status: str | None = None
    priority: str | None = None
    due_at: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    skill_required: str | None = Field(default=None, max_length=100)
    estimate_amount: Decimal | None = None
    labor_rate: Decimal | None = None
    # Optimistic concurrency token — required when changing status (M5)
    base_updated_at: datetime | None = None


class WorkOrderOut(BaseModel):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    service_location_id: UUID | None = None
    asset_id: UUID | None = None
    title: str
    description: str | None = None
    status: str
    priority: str
    due_at: datetime | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    skill_required: str | None = None
    estimate_amount: Decimal | None = None
    labor_rate: Decimal | None = None
    created_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    technician_id: UUID | None = None
    technician_name: str | None = None
    overlap_warning: bool = False
    overlapping_work_order_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class AssignmentCreate(BaseModel):
    work_order_id: UUID
    technician_id: UUID
    notes: str | None = None


class AssignmentOut(BaseModel):
    id: UUID
    organization_id: UUID
    work_order_id: UUID
    technician_id: UUID
    technician_name: str | None = None
    assigned_at: datetime
    notes: str | None = None
    work_order_title: str | None = None
    work_order_status: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    overlap_warning: bool = False
    overlapping_work_order_ids: list[UUID] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TechnicianOut(BaseModel):
    id: UUID
    display_name: str
    email: str
    skills: str | None = None
    role: str


class ScheduleItem(BaseModel):
    work_order_id: UUID
    title: str
    status: str
    priority: str
    customer_id: UUID
    technician_id: UUID | None = None
    technician_name: str | None = None
    scheduled_start: datetime | None = None
    scheduled_end: datetime | None = None
    due_at: datetime | None = None
    overlap_warning: bool = False
    overlapping_work_order_ids: list[UUID] = Field(default_factory=list)


class NoteCreate(BaseModel):
    note: str = Field(min_length=1)
    client_operation_id: UUID | None = None
    client_occurred_at: datetime | None = None


class JobActivityOut(BaseModel):
    id: UUID
    organization_id: UUID
    work_order_id: UUID
    actor_user_id: UUID | None = None
    activity_type: str
    note: str | None = None
    occurred_at: datetime
    client_operation_id: UUID | None = None
    client_occurred_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChecklistItemOut(BaseModel):
    id: UUID
    label: str
    is_required: bool
    is_completed: bool
    sort_order: int
    completed_at: datetime | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChecklistOut(BaseModel):
    id: UUID
    organization_id: UUID
    work_order_id: UUID
    name: str
    template_key: str | None = None
    items: list[ChecklistItemOut] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class ChecklistItemUpdate(BaseModel):
    is_completed: bool
    # Optimistic concurrency token — required (M5); mismatch → 409
    base_updated_at: datetime



class ChecklistCreate(BaseModel):
    work_order_id: UUID
    name: str = Field(min_length=1, max_length=200)
    template_key: str | None = Field(default=None, max_length=80)
    items: list[str] = Field(default_factory=list)


class TimeEntryCreate(BaseModel):
    work_order_id: UUID
    technician_id: UUID | None = None
    started_at: datetime
    ended_at: datetime | None = None
    minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None


class TimeEntryUpdate(BaseModel):
    started_at: datetime | None = None
    ended_at: datetime | None = None
    minutes: int | None = Field(default=None, ge=0)
    notes: str | None = None
    was_corrected: bool | None = None


class TimeEntryOut(BaseModel):
    id: UUID
    organization_id: UUID
    work_order_id: UUID
    technician_id: UUID
    started_at: datetime
    ended_at: datetime | None = None
    minutes: int | None = None
    notes: str | None = None
    was_corrected: bool

    model_config = {"from_attributes": True}

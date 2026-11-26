"""Service report and summary schemas."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.parts import PartUsedOut
from app.schemas.signoffs import SignoffOut
from app.schemas.work_orders import JobActivityOut, WorkOrderOut


class StatusCount(BaseModel):
    status: str
    count: int


class TechnicianLaborRow(BaseModel):
    technician_id: UUID | None = None
    technician_name: str | None = None
    total_minutes: int
    entry_count: int


class PartsSummaryRow(BaseModel):
    part_name: str
    total_quantity: Decimal
    total_cost: Decimal | None = None


class ServiceSummaryReport(BaseModel):
    jobs_by_status: list[StatusCount]
    total_jobs: int
    completed_jobs: int
    completion_rate: float
    labor: list[TechnicianLaborRow]
    total_labor_minutes: int
    parts: list[PartsSummaryRow]
    parts_total_cost: Decimal | None = None
    generated_at: datetime


class ChecklistItemReport(BaseModel):
    label: str
    is_completed: bool
    is_required: bool


class ChecklistReport(BaseModel):
    name: str
    items: list[ChecklistItemReport] = Field(default_factory=list)


class TimeEntryReport(BaseModel):
    technician_name: str | None = None
    started_at: datetime
    ended_at: datetime | None = None
    minutes: int | None = None
    notes: str | None = None


class PrintableServiceReport(BaseModel):
    """Aggregated payload for browser-print service report (no paid PDF)."""

    work_order: WorkOrderOut
    customer_name: str | None = None
    location_label: str | None = None
    asset_name: str | None = None
    notes: list[JobActivityOut] = Field(default_factory=list)
    checklists: list[ChecklistReport] = Field(default_factory=list)
    time_entries: list[TimeEntryReport] = Field(default_factory=list)
    parts: list[PartUsedOut] = Field(default_factory=list)
    signoffs: list[SignoffOut] = Field(default_factory=list)
    labor_minutes_total: int = 0
    parts_cost_total: Decimal | None = None
    print_hint: str = "Use browser Print (Ctrl/Cmd+P). No paid PDF API required."

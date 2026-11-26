"""Typed AI request/response schemas for Field Service Milestone 3."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import AISource


class ServiceReportSection(BaseModel):
    problem: str = ""
    diagnosis: str = ""
    work_performed: str = ""
    parts: list[str] = Field(default_factory=list)
    follow_up: str = ""


class ServiceReportDraftRequest(BaseModel):
    work_order_id: UUID
    notes: str | None = None
    transcript: str | None = None


class ServiceReportDraftResponse(BaseModel):
    work_order_id: UUID
    draft: ServiceReportSection
    explanation: str
    sources: list[AISource] = Field(default_factory=list)
    requires_confirmation: bool = True
    provider: str
    ai_cannot: list[str] = Field(
        default_factory=lambda: [
            "complete_job",
            "certify_safety",
            "sign_for_customer",
        ]
    )


class ServiceReportApproveRequest(BaseModel):
    work_order_id: UUID
    problem: str
    diagnosis: str
    work_performed: str
    parts: list[str] = Field(default_factory=list)
    follow_up: str = ""
    edited: bool = True


class ServiceReportApproveResponse(BaseModel):
    work_order_id: UUID
    approved: bool = True
    attachment_id: UUID | None = None
    audit_event_id: UUID | None = None
    status_unchanged: str
    message: str


class JobPrepRequest(BaseModel):
    work_order_id: UUID
    job_type: str | None = None


class ChecklistSuggestion(BaseModel):
    label: str
    reason: str
    confirmed: bool = False


class JobPrepResponse(BaseModel):
    work_order_id: UUID
    summary: str
    history_highlights: list[str] = Field(default_factory=list)
    existing_checklist: list[str] = Field(default_factory=list)
    suggested_checklist: list[ChecklistSuggestion] = Field(default_factory=list)
    explanation: str
    sources: list[AISource] = Field(default_factory=list)
    requires_confirmation: bool = True
    provider: str


class ConfirmChecklistRequest(BaseModel):
    work_order_id: UUID
    items: list[str] = Field(min_length=1)


class ConfirmChecklistResponse(BaseModel):
    work_order_id: UUID
    checklist_id: UUID
    added_labels: list[str]
    message: str


class ServiceMemorySearchRequest(BaseModel):
    query: str = ""
    asset_id: UUID | None = None
    customer_id: UUID | None = None
    limit: int = Field(default=20, ge=1, le=50)


class ServiceMemoryHit(BaseModel):
    work_order_id: UUID
    title: str
    status: str
    customer_id: UUID
    customer_name: str | None = None
    asset_id: UUID | None = None
    asset_name: str | None = None
    note_excerpt: str | None = None
    occurred_at: str | None = None


class ServiceMemoryResponse(BaseModel):
    query: str
    recurring_themes: list[str] = Field(default_factory=list)
    suggested_follow_up: str = ""
    hits: list[ServiceMemoryHit] = Field(default_factory=list)
    explanation: str
    sources: list[AISource] = Field(default_factory=list)
    requires_confirmation: bool = True
    provider: str
    result: dict[str, Any] = Field(default_factory=dict)

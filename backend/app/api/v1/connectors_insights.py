"""Read-only Insights connector facade over service summary aggregates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header

from app.api.deps import DbSession, require_roles
from app.api.errors import api_error
from app.core.config import settings
from app.models import User
from app.models.enums import UserRole
from app.schemas.reports import ServiceSummaryReport
from app.services.service_summary import build_service_summary
from starlette import status

router = APIRouter(prefix="/connectors/insights/v1", tags=["connectors-insights"])

StaffUser = Annotated[User, Depends(require_roles(UserRole.ADMIN, UserRole.DISPATCHER))]


def enforce_connector_key(
    x_connector_key: Annotated[str | None, Header(alias="X-Connector-Key")] = None,
) -> None:
    expected = (settings.insights_connector_key or "").strip()
    if not expected:
        return
    if not x_connector_key or x_connector_key.strip() != expected:
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_connector_key",
            "Missing or invalid X-Connector-Key",
        )


@router.get("/health")
def connector_health(
    _user: StaffUser,
    _: Annotated[None, Depends(enforce_connector_key)] = None,
) -> dict[str, str]:
    return {
        "status": "ok",
        "product": "field-service",
        "connector": "insights",
        "version": "v1",
        "milestone": "6",
    }


@router.get("/summary")
def connector_summary(
    user: StaffUser,
    db: DbSession,
    _: Annotated[None, Depends(enforce_connector_key)] = None,
) -> dict:
    summary = build_service_summary(db, user.organization_id)
    return _summary_payload(summary, user.organization_id)


@router.get("/jobs-by-status")
def connector_jobs_by_status(
    user: StaffUser,
    db: DbSession,
    _: Annotated[None, Depends(enforce_connector_key)] = None,
) -> dict:
    summary = build_service_summary(db, user.organization_id)
    return {
        "jobs_by_status": [r.model_dump(mode="json") for r in summary.jobs_by_status],
        "total_jobs": summary.total_jobs,
        "generated_at": _iso(summary.generated_at),
    }


@router.get("/completion")
def connector_completion(
    user: StaffUser,
    db: DbSession,
    _: Annotated[None, Depends(enforce_connector_key)] = None,
) -> dict:
    summary = build_service_summary(db, user.organization_id)
    return {
        "total_jobs": summary.total_jobs,
        "completed_jobs": summary.completed_jobs,
        "completion_rate": summary.completion_rate,
        "generated_at": _iso(summary.generated_at),
    }


@router.get("/labor")
def connector_labor(
    user: StaffUser,
    db: DbSession,
    _: Annotated[None, Depends(enforce_connector_key)] = None,
) -> dict:
    summary = build_service_summary(db, user.organization_id)
    return {
        "labor": [r.model_dump(mode="json") for r in summary.labor],
        "total_labor_minutes": summary.total_labor_minutes,
        "generated_at": _iso(summary.generated_at),
    }


@router.get("/parts")
def connector_parts(
    user: StaffUser,
    db: DbSession,
    _: Annotated[None, Depends(enforce_connector_key)] = None,
) -> dict:
    summary = build_service_summary(db, user.organization_id)
    return {
        "parts": [r.model_dump(mode="json") for r in summary.parts],
        "parts_total_cost": (
            str(summary.parts_total_cost) if summary.parts_total_cost is not None else None
        ),
        "generated_at": _iso(summary.generated_at),
    }


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat().replace("+00:00", "Z")


def _summary_payload(summary: ServiceSummaryReport, organization_id: UUID) -> dict:
    return {
        "source_product": "field-service",
        "connector_version": "v1",
        "organization_id": str(organization_id),
        "jobs_by_status": [r.model_dump(mode="json") for r in summary.jobs_by_status],
        "total_jobs": summary.total_jobs,
        "completed_jobs": summary.completed_jobs,
        "completion_rate": summary.completion_rate,
        "labor": [r.model_dump(mode="json") for r in summary.labor],
        "total_labor_minutes": summary.total_labor_minutes,
        "parts": [r.model_dump(mode="json") for r in summary.parts],
        "parts_total_cost": (
            str(summary.parts_total_cost) if summary.parts_total_cost is not None else None
        ),
        "generated_at": _iso(summary.generated_at),
    }


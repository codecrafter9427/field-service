"""Shared service summary aggregates for reports + Insights connector."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import PartUsed, TimeEntry, User, WorkOrder
from app.models.enums import WorkOrderStatus
from app.schemas.reports import (
    PartsSummaryRow,
    ServiceSummaryReport,
    StatusCount,
    TechnicianLaborRow,
)


def build_service_summary(db: Session, organization_id: UUID) -> ServiceSummaryReport:
    status_rows = db.execute(
        select(WorkOrder.status, func.count())
        .where(
            WorkOrder.organization_id == organization_id,
            WorkOrder.archived_at.is_(None),
        )
        .group_by(WorkOrder.status)
    ).all()
    by_status = [StatusCount(status=s, count=int(c)) for s, c in status_rows]
    total_jobs = sum(r.count for r in by_status)
    completed_jobs = next(
        (r.count for r in by_status if r.status == WorkOrderStatus.COMPLETED.value),
        0,
    )
    completion_rate = (
        round((completed_jobs / total_jobs) * 100.0, 1) if total_jobs else 0.0
    )

    labor_rows = db.execute(
        select(
            TimeEntry.technician_id,
            func.coalesce(func.sum(TimeEntry.minutes), 0),
            func.count(TimeEntry.id),
        )
        .where(TimeEntry.organization_id == organization_id)
        .group_by(TimeEntry.technician_id)
    ).all()
    labor: list[TechnicianLaborRow] = []
    total_minutes = 0
    for tech_id, minutes, entry_count in labor_rows:
        tech = db.get(User, tech_id) if tech_id else None
        mins = int(minutes or 0)
        total_minutes += mins
        labor.append(
            TechnicianLaborRow(
                technician_id=tech_id,
                technician_name=tech.display_name if tech else None,
                total_minutes=mins,
                entry_count=int(entry_count),
            )
        )
    labor.sort(key=lambda r: r.total_minutes, reverse=True)

    part_rows = db.execute(
        select(
            PartUsed.part_name,
            func.sum(PartUsed.quantity),
            func.sum(PartUsed.quantity * func.coalesce(PartUsed.unit_cost, 0)),
        )
        .where(PartUsed.organization_id == organization_id)
        .group_by(PartUsed.part_name)
    ).all()
    parts: list[PartsSummaryRow] = []
    parts_total: Decimal = Decimal("0")
    for name, qty, cost in part_rows:
        qty_d = Decimal(str(qty or 0))
        cost_d = Decimal(str(cost or 0)).quantize(Decimal("0.01"))
        parts_total += cost_d
        parts.append(
            PartsSummaryRow(
                part_name=name,
                total_quantity=qty_d,
                total_cost=cost_d if cost_d > 0 else None,
            )
        )
    parts.sort(key=lambda r: r.part_name)

    return ServiceSummaryReport(
        jobs_by_status=sorted(by_status, key=lambda r: r.status),
        total_jobs=total_jobs,
        completed_jobs=completed_jobs,
        completion_rate=completion_rate,
        labor=labor,
        total_labor_minutes=total_minutes,
        parts=parts,
        parts_total_cost=parts_total if parts_total > 0 else None,
        generated_at=datetime.now(timezone.utc),
    )

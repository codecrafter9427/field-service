"""Service reports — status/labor/parts summaries + printable job report data."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import not_found
from app.api.v1.work_orders import _to_out as work_order_to_out
from app.models import (
    Asset,
    Checklist,
    ChecklistItem,
    Customer,
    CustomerSignoff,
    JobActivity,
    PartUsed,
    ServiceLocation,
    TimeEntry,
    User,
    WorkOrder,
)
from app.models.enums import WorkOrderStatus
from app.schemas.parts import PartUsedOut
from app.schemas.reports import (
    ChecklistItemReport,
    ChecklistReport,
    PartsSummaryRow,
    PrintableServiceReport,
    ServiceSummaryReport,
    StatusCount,
    TechnicianLaborRow,
    TimeEntryReport,
)
from app.schemas.signoffs import SignoffOut
from app.schemas.work_orders import JobActivityOut

router = APIRouter()


@router.get("/service", response_model=ServiceSummaryReport)
def service_summary(user: CurrentUser, db: DbSession) -> ServiceSummaryReport:
    org_id = user.organization_id
    status_rows = db.execute(
        select(WorkOrder.status, func.count())
        .where(
            WorkOrder.organization_id == org_id,
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
        .where(TimeEntry.organization_id == org_id)
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
        .where(PartUsed.organization_id == org_id)
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


@router.get("/service/work-orders/{work_order_id}", response_model=PrintableServiceReport)
def printable_service_report(
    work_order_id: UUID, user: CurrentUser, db: DbSession
) -> PrintableServiceReport:
    wo = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.organization_id == user.organization_id,
            WorkOrder.archived_at.is_(None),
        )
    )
    if wo is None:
        raise not_found("Work order")

    customer = db.get(Customer, wo.customer_id)
    location = (
        db.get(ServiceLocation, wo.service_location_id)
        if wo.service_location_id
        else None
    )
    asset = db.get(Asset, wo.asset_id) if wo.asset_id else None

    notes = db.scalars(
        select(JobActivity)
        .where(
            JobActivity.work_order_id == wo.id,
            JobActivity.organization_id == user.organization_id,
            JobActivity.activity_type == "note",
        )
        .order_by(JobActivity.occurred_at.asc())
    ).all()

    checklists_out: list[ChecklistReport] = []
    checklists = db.scalars(
        select(Checklist).where(
            Checklist.work_order_id == wo.id,
            Checklist.organization_id == user.organization_id,
        )
    ).all()
    for cl in checklists:
        items = db.scalars(
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == cl.id)
            .order_by(ChecklistItem.sort_order.asc())
        ).all()
        checklists_out.append(
            ChecklistReport(
                name=cl.name,
                items=[
                    ChecklistItemReport(
                        label=i.label,
                        is_completed=i.is_completed,
                        is_required=i.is_required,
                    )
                    for i in items
                ],
            )
        )

    time_rows = db.scalars(
        select(TimeEntry)
        .where(
            TimeEntry.work_order_id == wo.id,
            TimeEntry.organization_id == user.organization_id,
        )
        .order_by(TimeEntry.started_at.asc())
    ).all()
    time_out: list[TimeEntryReport] = []
    labor_total = 0
    for t in time_rows:
        tech = db.get(User, t.technician_id)
        mins = t.minutes or 0
        labor_total += mins
        time_out.append(
            TimeEntryReport(
                technician_name=tech.display_name if tech else None,
                started_at=t.started_at,
                ended_at=t.ended_at,
                minutes=t.minutes,
                notes=t.notes,
            )
        )

    parts_rows = db.scalars(
        select(PartUsed).where(
            PartUsed.work_order_id == wo.id,
            PartUsed.organization_id == user.organization_id,
        )
    ).all()
    parts_out: list[PartUsedOut] = []
    parts_cost: Decimal = Decimal("0")
    for p in parts_rows:
        line = None
        if p.unit_cost is not None:
            line = (p.unit_cost * p.quantity).quantize(Decimal("0.01"))
            parts_cost += line
        parts_out.append(
            PartUsedOut(
                id=p.id,
                organization_id=p.organization_id,
                work_order_id=p.work_order_id,
                part_name=p.part_name,
                quantity=p.quantity,
                unit_cost=p.unit_cost,
                notes=p.notes,
                line_total=line,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    signoff_rows = db.scalars(
        select(CustomerSignoff)
        .where(
            CustomerSignoff.work_order_id == wo.id,
            CustomerSignoff.organization_id == user.organization_id,
        )
        .order_by(CustomerSignoff.signed_at.desc())
    ).all()
    signoffs = [
        SignoffOut(
            id=s.id,
            organization_id=s.organization_id,
            work_order_id=s.work_order_id,
            signer_name=s.signer_name,
            signed_at=s.signed_at,
            acknowledgement_text=s.acknowledgement_text,
            signature_storage_key=s.signature_storage_key,
            is_certified_esignature=False,
            created_at=s.created_at,
            updated_at=s.updated_at,
        )
        for s in signoff_rows
    ]

    location_label = None
    if location is not None:
        location_label = (
            f"{location.name} — {location.address_line1}, {location.city}"
        )

    return PrintableServiceReport(
        work_order=work_order_to_out(db, wo),
        customer_name=customer.name if customer else None,
        location_label=location_label,
        asset_name=asset.name if asset else None,
        notes=[JobActivityOut.model_validate(n) for n in notes],
        checklists=checklists_out,
        time_entries=time_out,
        parts=parts_out,
        signoffs=signoffs,
        labor_minutes_total=labor_total,
        parts_cost_total=parts_cost if parts_cost > 0 else None,
    )

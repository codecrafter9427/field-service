"""Build redacted customer job-status payloads from portal links."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    Asset,
    Checklist,
    ChecklistItem,
    Customer,
    CustomerSignoff,
    PartUsed,
    ServiceLocation,
    WorkOrder,
)
from app.models.portal import CustomerPortalLink
from app.schemas.portal import (
    ChecklistProgressPublic,
    CustomerJobStatusOut,
    PortalPartPublic,
)


def build_customer_job_status(
    db: Session, link: CustomerPortalLink, wo: WorkOrder
) -> CustomerJobStatusOut:
    customer = db.get(Customer, wo.customer_id)
    location = (
        db.get(ServiceLocation, wo.service_location_id) if wo.service_location_id else None
    )
    asset = db.get(Asset, wo.asset_id) if wo.asset_id else None

    location_label = None
    if location is not None:
        location_label = f"{location.name} — {location.address_line1}, {location.city}"

    summary = None
    if wo.description:
        summary = wo.description.strip()
        if len(summary) > 280:
            summary = summary[:277] + "..."

    checklist_ids = list(
        db.scalars(
            select(Checklist.id).where(
                Checklist.work_order_id == wo.id,
                Checklist.organization_id == link.organization_id,
            )
        ).all()
    )
    progress = None
    if checklist_ids:
        total = db.scalar(
            select(func.count())
            .select_from(ChecklistItem)
            .where(ChecklistItem.checklist_id.in_(checklist_ids))
        ) or 0
        completed = db.scalar(
            select(func.count())
            .select_from(ChecklistItem)
            .where(
                ChecklistItem.checklist_id.in_(checklist_ids),
                ChecklistItem.is_completed.is_(True),
            )
        ) or 0
        progress = ChecklistProgressPublic(completed=int(completed), total=int(total))

    parts_rows = db.scalars(
        select(PartUsed).where(
            PartUsed.work_order_id == wo.id,
            PartUsed.organization_id == link.organization_id,
        )
    ).all()
    parts = [
        PortalPartPublic(part_name=p.part_name, quantity=p.quantity) for p in parts_rows
    ]

    latest_signoff = db.scalar(
        select(CustomerSignoff)
        .where(
            CustomerSignoff.work_order_id == wo.id,
            CustomerSignoff.organization_id == link.organization_id,
        )
        .order_by(CustomerSignoff.signed_at.desc())
        .limit(1)
    )

    return CustomerJobStatusOut(
        work_order_id=wo.id,
        title=wo.title,
        status=wo.status,
        scheduled_start=wo.scheduled_start,
        scheduled_end=wo.scheduled_end,
        customer_name=customer.name if customer else None,
        location_label=location_label,
        asset_name=asset.name if asset else None,
        service_summary=summary,
        checklist_progress=progress,
        parts=parts,
        acknowledgement_recorded=latest_signoff is not None,
        acknowledged_at=latest_signoff.signed_at if latest_signoff else None,
        generated_at=datetime.now(timezone.utc),
        link_expires_at=link.expires_at,
    )

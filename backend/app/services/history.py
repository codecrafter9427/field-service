"""Service history helpers for customer/asset views."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, Customer, JobActivity, WorkOrder
from app.schemas.assets import ServiceHistoryItem


def service_history(
    db: Session,
    *,
    organization_id: UUID,
    asset_id: UUID | None = None,
    customer_id: UUID | None = None,
    limit: int = 100,
) -> list[ServiceHistoryItem]:
    filters = [
        WorkOrder.organization_id == organization_id,
        WorkOrder.archived_at.is_(None),
    ]
    if asset_id is not None:
        filters.append(WorkOrder.asset_id == asset_id)
    if customer_id is not None:
        filters.append(WorkOrder.customer_id == customer_id)

    rows = db.scalars(
        select(WorkOrder)
        .where(*filters)
        .order_by(WorkOrder.updated_at.desc())
        .limit(limit)
    ).all()
    items: list[ServiceHistoryItem] = []
    for wo in rows:
        customer = db.get(Customer, wo.customer_id)
        asset = db.get(Asset, wo.asset_id) if wo.asset_id else None
        note_row = db.scalar(
            select(JobActivity)
            .where(
                JobActivity.work_order_id == wo.id,
                JobActivity.activity_type == "note",
            )
            .order_by(JobActivity.occurred_at.desc())
            .limit(1)
        )
        items.append(
            ServiceHistoryItem(
                work_order_id=wo.id,
                title=wo.title,
                status=wo.status,
                priority=wo.priority,
                customer_id=wo.customer_id,
                customer_name=customer.name if customer else None,
                asset_id=wo.asset_id,
                asset_name=asset.name if asset else None,
                scheduled_start=wo.scheduled_start,
                completed_note=note_row.note if note_row else None,
                updated_at=wo.updated_at,
            )
        )
    return items

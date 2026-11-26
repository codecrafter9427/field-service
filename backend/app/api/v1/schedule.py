"""Schedule / dispatch list with overlap warnings."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import or_, select

from app.api.deps import CurrentUser, DbSession
from app.models import User, WorkOrder, WorkOrderAssignment
from app.models.enums import WorkOrderStatus
from app.schemas.work_orders import ScheduleItem
from app.services.overlap import find_overlapping_work_orders

router = APIRouter()


@router.get("", response_model=list[ScheduleItem])
def list_schedule(
    user: CurrentUser,
    db: DbSession,
    from_at: datetime | None = Query(None, alias="from"),
    to_at: datetime | None = Query(None, alias="to"),
    technician_id: UUID | None = Query(None),
) -> list[ScheduleItem]:
    """List scheduled jobs for the org; flags overlapping technician windows."""
    filters = [
        WorkOrder.organization_id == user.organization_id,
        WorkOrder.archived_at.is_(None),
        WorkOrder.status != WorkOrderStatus.CANCELLED.value,
    ]
    if from_at is not None:
        filters.append(
            or_(
                WorkOrder.scheduled_end.is_(None),
                WorkOrder.scheduled_end >= from_at,
            )
        )
    if to_at is not None:
        filters.append(
            or_(
                WorkOrder.scheduled_start.is_(None),
                WorkOrder.scheduled_start <= to_at,
            )
        )

    work_orders = db.scalars(
        select(WorkOrder)
        .where(*filters)
        .order_by(WorkOrder.scheduled_start.asc().nulls_last(), WorkOrder.due_at.asc())
    ).all()

    items: list[ScheduleItem] = []
    for wo in work_orders:
        assignment = db.scalar(
            select(WorkOrderAssignment)
            .where(WorkOrderAssignment.work_order_id == wo.id)
            .order_by(WorkOrderAssignment.assigned_at.desc())
            .limit(1)
        )
        if technician_id is not None:
            if assignment is None or assignment.technician_id != technician_id:
                continue

        tech_id = assignment.technician_id if assignment else None
        tech_name = None
        overlaps: list[UUID] = []
        if tech_id is not None:
            tech = db.get(User, tech_id)
            tech_name = tech.display_name if tech else None
            if wo.scheduled_start and wo.scheduled_end:
                overlaps = find_overlapping_work_orders(
                    db,
                    organization_id=user.organization_id,
                    technician_id=tech_id,
                    scheduled_start=wo.scheduled_start,
                    scheduled_end=wo.scheduled_end,
                    exclude_work_order_id=wo.id,
                )

        items.append(
            ScheduleItem(
                work_order_id=wo.id,
                title=wo.title,
                status=wo.status,
                priority=wo.priority,
                customer_id=wo.customer_id,
                technician_id=tech_id,
                technician_name=tech_name,
                scheduled_start=wo.scheduled_start,
                scheduled_end=wo.scheduled_end,
                due_at=wo.due_at,
                overlap_warning=bool(overlaps),
                overlapping_work_order_ids=overlaps,
            )
        )
    return items

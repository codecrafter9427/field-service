"""Server-side overlap detection for technician schedules."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import WorkOrder, WorkOrderAssignment
from app.models.enums import WorkOrderStatus

# Statuses that still occupy a technician's calendar
ACTIVE_SCHEDULE_STATUSES = {
    WorkOrderStatus.DRAFT.value,
    WorkOrderStatus.SCHEDULED.value,
    WorkOrderStatus.EN_ROUTE.value,
    WorkOrderStatus.IN_PROGRESS.value,
    WorkOrderStatus.WAITING_FOR_PARTS.value,
}


def intervals_overlap(
    start_a: datetime | None,
    end_a: datetime | None,
    start_b: datetime | None,
    end_b: datetime | None,
) -> bool:
    """Return True when both intervals are fully specified and overlap."""
    if start_a is None or end_a is None or start_b is None or end_b is None:
        return False
    return start_a < end_b and start_b < end_a


def find_overlapping_work_orders(
    db: Session,
    *,
    organization_id: UUID,
    technician_id: UUID,
    scheduled_start: datetime | None,
    scheduled_end: datetime | None,
    exclude_work_order_id: UUID | None = None,
) -> list[UUID]:
    """Return work order IDs assigned to the technician that overlap the window."""
    if scheduled_start is None or scheduled_end is None:
        return []
    if scheduled_end <= scheduled_start:
        return []

    stmt = (
        select(WorkOrder)
        .join(
            WorkOrderAssignment,
            WorkOrderAssignment.work_order_id == WorkOrder.id,
        )
        .where(
            WorkOrder.organization_id == organization_id,
            WorkOrder.archived_at.is_(None),
            WorkOrder.status.in_(ACTIVE_SCHEDULE_STATUSES),
            WorkOrderAssignment.technician_id == technician_id,
            WorkOrderAssignment.organization_id == organization_id,
            WorkOrder.scheduled_start.is_not(None),
            WorkOrder.scheduled_end.is_not(None),
        )
    )
    if exclude_work_order_id is not None:
        stmt = stmt.where(WorkOrder.id != exclude_work_order_id)

    overlaps: list[UUID] = []
    for wo in db.scalars(stmt).all():
        if intervals_overlap(
            scheduled_start, scheduled_end, wo.scheduled_start, wo.scheduled_end
        ):
            overlaps.append(wo.id)
    return overlaps

"""Assignments and technician agenda."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import bad_request, not_found
from app.models import User, WorkOrder, WorkOrderAssignment
from app.models.enums import JobActivityType, UserRole, WorkOrderStatus
from app.models.work_order import JobActivity
from app.schemas.common import Page, PageMeta
from app.schemas.work_orders import (
    AssignmentCreate,
    AssignmentOut,
    TechnicianOut,
)
from app.services.overlap import find_overlapping_work_orders

router = APIRouter()


def _to_assignment_out(
    db: DbSession,
    assignment: WorkOrderAssignment,
    work_order: WorkOrder | None = None,
) -> AssignmentOut:
    wo = work_order or db.get(WorkOrder, assignment.work_order_id)
    tech = db.get(User, assignment.technician_id)
    overlaps: list[UUID] = []
    if (
        wo is not None
        and wo.scheduled_start is not None
        and wo.scheduled_end is not None
        and wo.status != WorkOrderStatus.CANCELLED.value
    ):
        overlaps = find_overlapping_work_orders(
            db,
            organization_id=assignment.organization_id,
            technician_id=assignment.technician_id,
            scheduled_start=wo.scheduled_start,
            scheduled_end=wo.scheduled_end,
            exclude_work_order_id=wo.id,
        )
    return AssignmentOut(
        id=assignment.id,
        organization_id=assignment.organization_id,
        work_order_id=assignment.work_order_id,
        technician_id=assignment.technician_id,
        technician_name=tech.display_name if tech else None,
        assigned_at=assignment.assigned_at,
        notes=assignment.notes,
        work_order_title=wo.title if wo else None,
        work_order_status=wo.status if wo else None,
        scheduled_start=wo.scheduled_start if wo else None,
        scheduled_end=wo.scheduled_end if wo else None,
        overlap_warning=bool(overlaps),
        overlapping_work_order_ids=overlaps,
    )


@router.get("/technicians", response_model=list[TechnicianOut])
def list_technicians(user: CurrentUser, db: DbSession) -> list[TechnicianOut]:
    rows = db.scalars(
        select(User)
        .where(
            User.organization_id == user.organization_id,
            User.archived_at.is_(None),
            User.is_active.is_(True),
            User.role == UserRole.TECHNICIAN.value,
        )
        .order_by(User.display_name)
    ).all()
    return [
        TechnicianOut(
            id=r.id,
            display_name=r.display_name,
            email=r.email,
            skills=r.skills,
            role=r.role,
        )
        for r in rows
    ]


@router.get("", response_model=Page[AssignmentOut])
def list_assignments(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    technician_id: UUID | None = Query(None),
) -> Page[AssignmentOut]:
    filters = [WorkOrderAssignment.organization_id == user.organization_id]
    if technician_id is not None:
        filters.append(WorkOrderAssignment.technician_id == technician_id)

    # Latest assignment per work order via distinct-on style: fetch then dedupe
    rows = db.scalars(
        select(WorkOrderAssignment)
        .where(*filters)
        .order_by(
            WorkOrderAssignment.work_order_id,
            WorkOrderAssignment.assigned_at.desc(),
        )
    ).all()

    seen: set[UUID] = set()
    latest: list[WorkOrderAssignment] = []
    for row in rows:
        if row.work_order_id in seen:
            continue
        seen.add(row.work_order_id)
        latest.append(row)

    total = len(latest)
    start = (page - 1) * page_size
    page_rows = latest[start : start + page_size]
    return Page(
        items=[_to_assignment_out(db, r) for r in page_rows],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/agenda", response_model=list[AssignmentOut])
def technician_agenda(
    user: CurrentUser,
    db: DbSession,
    technician_id: UUID | None = Query(None),
) -> list[AssignmentOut]:
    """Agenda for a technician (defaults to current user when role=technician)."""
    target_id = technician_id
    if target_id is None:
        if user.role != UserRole.TECHNICIAN.value:
            raise bad_request(
                "technician_id_required",
                "technician_id is required for dispatcher/admin agenda queries",
            )
        target_id = user.id

    tech = db.scalar(
        select(User).where(
            User.id == target_id,
            User.organization_id == user.organization_id,
            User.archived_at.is_(None),
        )
    )
    if tech is None:
        raise not_found("Technician")

    rows = db.scalars(
        select(WorkOrderAssignment)
        .where(
            WorkOrderAssignment.organization_id == user.organization_id,
            WorkOrderAssignment.technician_id == target_id,
        )
        .order_by(WorkOrderAssignment.assigned_at.desc())
    ).all()

    seen: set[UUID] = set()
    agenda: list[AssignmentOut] = []
    for assignment in rows:
        if assignment.work_order_id in seen:
            continue
        seen.add(assignment.work_order_id)
        wo = db.get(WorkOrder, assignment.work_order_id)
        if wo is None or wo.archived_at is not None:
            continue
        if wo.status == WorkOrderStatus.CANCELLED.value:
            continue
        agenda.append(_to_assignment_out(db, assignment, wo))

    def _sort_key(a: AssignmentOut) -> datetime:
        if a.scheduled_start is not None:
            return a.scheduled_start
        return a.assigned_at

    agenda.sort(key=_sort_key)
    return agenda


@router.post("", response_model=AssignmentOut, status_code=201)
def create_assignment(
    body: AssignmentCreate, user: CurrentUser, db: DbSession
) -> AssignmentOut:
    wo = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == body.work_order_id,
            WorkOrder.organization_id == user.organization_id,
            WorkOrder.archived_at.is_(None),
        )
    )
    if wo is None:
        raise not_found("Work order")

    tech = db.scalar(
        select(User).where(
            User.id == body.technician_id,
            User.organization_id == user.organization_id,
            User.is_active.is_(True),
            User.archived_at.is_(None),
            User.role == UserRole.TECHNICIAN.value,
        )
    )
    if tech is None:
        raise bad_request(
            "invalid_technician",
            "Technician not found in your organization",
        )

    overlaps = find_overlapping_work_orders(
        db,
        organization_id=user.organization_id,
        technician_id=body.technician_id,
        scheduled_start=wo.scheduled_start,
        scheduled_end=wo.scheduled_end,
        exclude_work_order_id=wo.id,
    )

    assignment = WorkOrderAssignment(
        organization_id=user.organization_id,
        work_order_id=wo.id,
        technician_id=body.technician_id,
        notes=body.notes,
    )
    db.add(assignment)
    db.add(
        JobActivity(
            organization_id=user.organization_id,
            work_order_id=wo.id,
            actor_user_id=user.id,
            activity_type=JobActivityType.ASSIGNMENT.value,
            note=f"Assigned to {tech.display_name}",
        )
    )
    if wo.status == WorkOrderStatus.DRAFT.value:
        wo.status = WorkOrderStatus.SCHEDULED.value
    db.commit()
    db.refresh(assignment)
    out = _to_assignment_out(db, assignment, wo)
    out.overlap_warning = bool(overlaps)
    out.overlapping_work_order_ids = overlaps
    return out

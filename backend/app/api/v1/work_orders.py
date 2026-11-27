"""Work orders — org-scoped CRUD, assign, notes, status."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query, Response
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, DbSession
from app.api.errors import bad_request, conflict, not_found
from app.models import (
    Customer,
    JobActivity,
    ServiceLocation,
    User,
    WorkOrder,
    WorkOrderAssignment,
)
from app.models.enums import JobActivityType, UserRole, WorkOrderPriority, WorkOrderStatus
from app.schemas.common import Page, PageMeta
from app.schemas.work_orders import (
    AssignmentOut,
    JobActivityOut,
    NoteCreate,
    WorkOrderCreate,
    WorkOrderOut,
    WorkOrderUpdate,
)
from app.services.overlap import find_overlapping_work_orders

router = APIRouter()

VALID_STATUSES = {s.value for s in WorkOrderStatus}
VALID_PRIORITIES = {p.value for p in WorkOrderPriority}


def _same_instant(server: datetime, base: datetime) -> bool:
    """Compare optimistic-concurrency tokens (tolerate serialization precision)."""
    s = server.astimezone(timezone.utc)
    b = base.astimezone(timezone.utc)
    return abs((s - b).total_seconds()) < 0.001


def _latest_assignment(
    db: Session, work_order_id: UUID
) -> WorkOrderAssignment | None:
    return db.scalar(
        select(WorkOrderAssignment)
        .where(WorkOrderAssignment.work_order_id == work_order_id)
        .order_by(WorkOrderAssignment.assigned_at.desc())
        .limit(1)
    )


def _technician_name(db: Session, technician_id: UUID | None) -> str | None:
    if technician_id is None:
        return None
    user = db.get(User, technician_id)
    return user.display_name if user else None


def _to_out(
    db: Session,
    row: WorkOrder,
    *,
    overlap_ids: list[UUID] | None = None,
) -> WorkOrderOut:
    assignment = _latest_assignment(db, row.id)
    tech_id = assignment.technician_id if assignment else None
    overlaps = overlap_ids
    if overlaps is None and tech_id and row.scheduled_start and row.scheduled_end:
        overlaps = find_overlapping_work_orders(
            db,
            organization_id=row.organization_id,
            technician_id=tech_id,
            scheduled_start=row.scheduled_start,
            scheduled_end=row.scheduled_end,
            exclude_work_order_id=row.id,
        )
    overlaps = overlaps or []
    return WorkOrderOut(
        id=row.id,
        organization_id=row.organization_id,
        customer_id=row.customer_id,
        service_location_id=row.service_location_id,
        asset_id=row.asset_id,
        title=row.title,
        description=row.description,
        status=row.status,
        priority=row.priority,
        due_at=row.due_at,
        scheduled_start=row.scheduled_start,
        scheduled_end=row.scheduled_end,
        skill_required=row.skill_required,
        estimate_amount=row.estimate_amount,
        labor_rate=row.labor_rate,
        created_by_id=row.created_by_id,
        created_at=row.created_at,
        updated_at=row.updated_at,
        technician_id=tech_id,
        technician_name=_technician_name(db, tech_id),
        overlap_warning=bool(overlaps),
        overlapping_work_order_ids=overlaps,
    )


def _get_work_order(db: DbSession, user: CurrentUser, work_order_id: UUID) -> WorkOrder:
    row = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.organization_id == user.organization_id,
            WorkOrder.archived_at.is_(None),
        )
    )
    if row is None:
        raise not_found("Work order")
    return row


def _ensure_customer(db: Session, org_id: UUID, customer_id: UUID) -> None:
    exists = db.scalar(
        select(Customer.id).where(
            Customer.id == customer_id,
            Customer.organization_id == org_id,
            Customer.archived_at.is_(None),
        )
    )
    if exists is None:
        raise bad_request("invalid_customer", "Customer not found in your organization")


def _ensure_location(
    db: Session, org_id: UUID, location_id: UUID | None, customer_id: UUID
) -> None:
    if location_id is None:
        return
    loc = db.scalar(
        select(ServiceLocation).where(
            ServiceLocation.id == location_id,
            ServiceLocation.organization_id == org_id,
            ServiceLocation.archived_at.is_(None),
        )
    )
    if loc is None:
        raise bad_request(
            "invalid_service_location",
            "Service location not found in your organization",
        )
    if loc.customer_id != customer_id:
        raise bad_request(
            "location_customer_mismatch",
            "Service location does not belong to the selected customer",
        )


def _ensure_technician(db: Session, org_id: UUID, technician_id: UUID) -> User:
    tech = db.scalar(
        select(User).where(
            User.id == technician_id,
            User.organization_id == org_id,
            User.is_active.is_(True),
            User.archived_at.is_(None),
            User.role.in_(
                [
                    UserRole.TECHNICIAN.value,
                    UserRole.ADMIN.value,
                    UserRole.DISPATCHER.value,
                ]
            ),
        )
    )
    if tech is None:
        raise bad_request(
            "invalid_technician",
            "Technician not found in your organization",
        )
    return tech


def _validate_window(start: datetime | None, end: datetime | None) -> None:
    if start is not None and end is not None and end <= start:
        raise bad_request(
            "invalid_schedule_window",
            "scheduled_end must be after scheduled_start",
        )


def _assign(
    db: Session,
    *,
    org_id: UUID,
    work_order: WorkOrder,
    technician_id: UUID,
    actor_id: UUID | None,
    notes: str | None = None,
) -> list[UUID]:
    _ensure_technician(db, org_id, technician_id)
    overlaps = find_overlapping_work_orders(
        db,
        organization_id=org_id,
        technician_id=technician_id,
        scheduled_start=work_order.scheduled_start,
        scheduled_end=work_order.scheduled_end,
        exclude_work_order_id=work_order.id,
    )
    db.add(
        WorkOrderAssignment(
            organization_id=org_id,
            work_order_id=work_order.id,
            technician_id=technician_id,
            notes=notes,
        )
    )
    db.add(
        JobActivity(
            organization_id=org_id,
            work_order_id=work_order.id,
            actor_user_id=actor_id,
            activity_type=JobActivityType.ASSIGNMENT.value,
            note=f"Assigned technician {technician_id}",
        )
    )
    if work_order.status == WorkOrderStatus.DRAFT.value:
        work_order.status = WorkOrderStatus.SCHEDULED.value
    return overlaps


@router.get("", response_model=Page[WorkOrderOut])
def list_work_orders(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
    customer_id: UUID | None = Query(None),
) -> Page[WorkOrderOut]:
    filters = [
        WorkOrder.organization_id == user.organization_id,
        WorkOrder.archived_at.is_(None),
    ]
    if status:
        filters.append(WorkOrder.status == status)
    if customer_id:
        filters.append(WorkOrder.customer_id == customer_id)

    total = db.scalar(select(func.count()).select_from(WorkOrder).where(*filters)) or 0
    rows = db.scalars(
        select(WorkOrder)
        .where(*filters)
        .order_by(WorkOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return Page(
        items=[_to_out(db, row) for row in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.post("", response_model=WorkOrderOut, status_code=201)
def create_work_order(
    body: WorkOrderCreate, user: CurrentUser, db: DbSession
) -> WorkOrderOut:
    if body.status not in VALID_STATUSES:
        raise bad_request("invalid_status", f"Unknown status: {body.status}")
    if body.priority not in VALID_PRIORITIES:
        raise bad_request("invalid_priority", f"Unknown priority: {body.priority}")
    _validate_window(body.scheduled_start, body.scheduled_end)
    _ensure_customer(db, user.organization_id, body.customer_id)
    _ensure_location(
        db, user.organization_id, body.service_location_id, body.customer_id
    )

    row = WorkOrder(
        organization_id=user.organization_id,
        customer_id=body.customer_id,
        service_location_id=body.service_location_id,
        asset_id=body.asset_id,
        title=body.title.strip(),
        description=body.description,
        status=body.status,
        priority=body.priority,
        due_at=body.due_at,
        scheduled_start=body.scheduled_start,
        scheduled_end=body.scheduled_end,
        skill_required=body.skill_required,
        estimate_amount=body.estimate_amount,
        labor_rate=body.labor_rate,
        created_by_id=user.id,
    )
    db.add(row)
    db.flush()

    overlaps: list[UUID] = []
    if body.technician_id is not None:
        overlaps = _assign(
            db,
            org_id=user.organization_id,
            work_order=row,
            technician_id=body.technician_id,
            actor_id=user.id,
        )

    db.add(
        JobActivity(
            organization_id=user.organization_id,
            work_order_id=row.id,
            actor_user_id=user.id,
            activity_type=JobActivityType.STATUS_CHANGE.value,
            note=f"Created with status {row.status}",
        )
    )
    db.commit()
    db.refresh(row)
    return _to_out(db, row, overlap_ids=overlaps)


@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(
    work_order_id: UUID, user: CurrentUser, db: DbSession
) -> WorkOrderOut:
    return _to_out(db, _get_work_order(db, user, work_order_id))


@router.patch("/{work_order_id}", response_model=WorkOrderOut)
def update_work_order(
    work_order_id: UUID,
    body: WorkOrderUpdate,
    user: CurrentUser,
    db: DbSession,
) -> WorkOrderOut:
    row = _get_work_order(db, user, work_order_id)
    data = body.model_dump(exclude_unset=True)
    base_updated_at = data.pop("base_updated_at", None)

    if "status" in data and data["status"] not in VALID_STATUSES:
        raise bad_request("invalid_status", f"Unknown status: {data['status']}")
    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        raise bad_request("invalid_priority", f"Unknown priority: {data['priority']}")

    # M5: status changes require optimistic concurrency — never silent overwrite
    if "status" in data:
        if base_updated_at is None:
            raise bad_request(
                "base_updated_at_required",
                "base_updated_at is required when updating status",
            )
        if not _same_instant(row.updated_at, base_updated_at):
            raise conflict(
                "Work order was modified by another client",
                details={"server": _to_out(db, row).model_dump(mode="json")},
            )

    new_start = data.get("scheduled_start", row.scheduled_start)
    new_end = data.get("scheduled_end", row.scheduled_end)
    _validate_window(new_start, new_end)

    if "customer_id" in data and data["customer_id"] is not None:
        _ensure_customer(db, user.organization_id, data["customer_id"])
    customer_id = data.get("customer_id", row.customer_id)
    if "service_location_id" in data:
        _ensure_location(
            db, user.organization_id, data["service_location_id"], customer_id
        )

    old_status = row.status
    if "title" in data and data["title"] is not None:
        data["title"] = data["title"].strip()
    for key, value in data.items():
        setattr(row, key, value)

    if "status" in data and data["status"] != old_status:
        db.add(
            JobActivity(
                organization_id=user.organization_id,
                work_order_id=row.id,
                actor_user_id=user.id,
                activity_type=JobActivityType.STATUS_CHANGE.value,
                note=f"Status changed from {old_status} to {row.status}",
            )
        )

    db.commit()
    db.refresh(row)
    return _to_out(db, row)


@router.delete("/{work_order_id}", status_code=204)
def archive_work_order(
    work_order_id: UUID, user: CurrentUser, db: DbSession
) -> None:
    row = _get_work_order(db, user, work_order_id)
    row.archived_at = datetime.now(tz=timezone.utc)
    db.commit()


@router.post("/{work_order_id}/assign", response_model=AssignmentOut)
def assign_technician(
    work_order_id: UUID,
    user: CurrentUser,
    db: DbSession,
    technician_id: UUID = Query(...),
    notes: str | None = Query(None),
) -> AssignmentOut:
    row = _get_work_order(db, user, work_order_id)
    tech = _ensure_technician(db, user.organization_id, technician_id)
    overlaps = _assign(
        db,
        org_id=user.organization_id,
        work_order=row,
        technician_id=technician_id,
        actor_id=user.id,
        notes=notes,
    )
    db.commit()
    assignment = _latest_assignment(db, row.id)
    assert assignment is not None
    return AssignmentOut(
        id=assignment.id,
        organization_id=assignment.organization_id,
        work_order_id=assignment.work_order_id,
        technician_id=assignment.technician_id,
        technician_name=tech.display_name,
        assigned_at=assignment.assigned_at,
        notes=assignment.notes,
        work_order_title=row.title,
        work_order_status=row.status,
        scheduled_start=row.scheduled_start,
        scheduled_end=row.scheduled_end,
        overlap_warning=bool(overlaps),
        overlapping_work_order_ids=overlaps,
    )


@router.get("/{work_order_id}/activities", response_model=list[JobActivityOut])
def list_activities(
    work_order_id: UUID, user: CurrentUser, db: DbSession
) -> list[JobActivityOut]:
    _get_work_order(db, user, work_order_id)
    rows = db.scalars(
        select(JobActivity)
        .where(
            JobActivity.work_order_id == work_order_id,
            JobActivity.organization_id == user.organization_id,
        )
        .order_by(JobActivity.occurred_at.desc())
    ).all()
    return [JobActivityOut.model_validate(r) for r in rows]


@router.post(
    "/{work_order_id}/notes",
    response_model=JobActivityOut,
    status_code=201,
)
def add_note(
    work_order_id: UUID,
    body: NoteCreate,
    user: CurrentUser,
    db: DbSession,
    response: Response,
) -> JobActivityOut:
    _get_work_order(db, user, work_order_id)

    # Idempotent replay: same client_operation_id → same activity (no duplicate)
    if body.client_operation_id is not None:
        existing = db.scalar(
            select(JobActivity).where(
                JobActivity.organization_id == user.organization_id,
                JobActivity.client_operation_id == body.client_operation_id,
            )
        )
        if existing is not None:
            response.status_code = 200
            return JobActivityOut.model_validate(existing)

    occurred = body.client_occurred_at or datetime.now(tz=timezone.utc)
    activity = JobActivity(
        organization_id=user.organization_id,
        work_order_id=work_order_id,
        actor_user_id=user.id,
        activity_type=JobActivityType.NOTE.value,
        note=body.note.strip(),
        client_operation_id=body.client_operation_id,
        client_occurred_at=body.client_occurred_at,
        occurred_at=occurred,
    )
    db.add(activity)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if body.client_operation_id is None:
            raise
        existing = db.scalar(
            select(JobActivity).where(
                JobActivity.organization_id == user.organization_id,
                JobActivity.client_operation_id == body.client_operation_id,
            )
        )
        if existing is None:
            raise
        response.status_code = 200
        return JobActivityOut.model_validate(existing)
    db.refresh(activity)
    return JobActivityOut.model_validate(activity)

"""Time entry basic APIs."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import bad_request, not_found
from app.models import JobActivity, TimeEntry, User, WorkOrder
from app.models.enums import JobActivityType
from app.schemas.work_orders import TimeEntryCreate, TimeEntryOut, TimeEntryUpdate

router = APIRouter()


def _ensure_work_order(db: DbSession, user: CurrentUser, work_order_id: UUID) -> WorkOrder:
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


@router.get("", response_model=list[TimeEntryOut])
def list_time_entries(
    user: CurrentUser,
    db: DbSession,
    work_order_id: UUID | None = Query(None),
) -> list[TimeEntryOut]:
    filters = [TimeEntry.organization_id == user.organization_id]
    if work_order_id is not None:
        filters.append(TimeEntry.work_order_id == work_order_id)
    rows = db.scalars(
        select(TimeEntry).where(*filters).order_by(TimeEntry.started_at.desc())
    ).all()
    return [TimeEntryOut.model_validate(r) for r in rows]


@router.post("", response_model=TimeEntryOut, status_code=201)
def create_time_entry(
    body: TimeEntryCreate, user: CurrentUser, db: DbSession
) -> TimeEntryOut:
    _ensure_work_order(db, user, body.work_order_id)
    tech_id = body.technician_id or user.id
    tech = db.scalar(
        select(User).where(
            User.id == tech_id,
            User.organization_id == user.organization_id,
            User.archived_at.is_(None),
        )
    )
    if tech is None:
        raise bad_request("invalid_technician", "Technician not found in your organization")

    if body.ended_at is not None and body.ended_at <= body.started_at:
        raise bad_request("invalid_time_range", "ended_at must be after started_at")

    minutes = body.minutes
    if minutes is None and body.ended_at is not None:
        minutes = int((body.ended_at - body.started_at).total_seconds() // 60)

    entry = TimeEntry(
        organization_id=user.organization_id,
        work_order_id=body.work_order_id,
        technician_id=tech_id,
        started_at=body.started_at,
        ended_at=body.ended_at,
        minutes=minutes,
        notes=body.notes,
    )
    db.add(entry)
    db.add(
        JobActivity(
            organization_id=user.organization_id,
            work_order_id=body.work_order_id,
            actor_user_id=user.id,
            activity_type=JobActivityType.TIME.value,
            note=f"Time entry recorded ({minutes or 0} min)",
        )
    )
    db.commit()
    db.refresh(entry)
    return TimeEntryOut.model_validate(entry)


@router.patch("/{entry_id}", response_model=TimeEntryOut)
def update_time_entry(
    entry_id: UUID,
    body: TimeEntryUpdate,
    user: CurrentUser,
    db: DbSession,
) -> TimeEntryOut:
    entry = db.scalar(
        select(TimeEntry).where(
            TimeEntry.id == entry_id,
            TimeEntry.organization_id == user.organization_id,
        )
    )
    if entry is None:
        raise not_found("Time entry")

    data = body.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(entry, key, value)

    started = entry.started_at
    ended = entry.ended_at
    if ended is not None and ended <= started:
        raise bad_request("invalid_time_range", "ended_at must be after started_at")
    if entry.minutes is None and ended is not None:
        entry.minutes = int((ended - started).total_seconds() // 60)
    if data:
        entry.was_corrected = True

    db.add(
        JobActivity(
            organization_id=user.organization_id,
            work_order_id=entry.work_order_id,
            actor_user_id=user.id,
            activity_type=JobActivityType.TIME.value,
            note="Time entry corrected",
        )
    )
    db.commit()
    db.refresh(entry)
    return TimeEntryOut.model_validate(entry)

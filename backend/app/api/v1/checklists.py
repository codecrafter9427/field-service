"""Checklists and checklist item updates."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import conflict, not_found
from app.models import Checklist, ChecklistItem, JobActivity, WorkOrder
from app.models.enums import JobActivityType
from app.schemas.work_orders import (
    ChecklistCreate,
    ChecklistItemOut,
    ChecklistItemUpdate,
    ChecklistOut,
)

router = APIRouter()


def _same_instant(server: datetime, base: datetime) -> bool:
    s = server.astimezone(timezone.utc)
    b = base.astimezone(timezone.utc)
    return abs((s - b).total_seconds()) < 0.001


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


def _to_out(checklist: Checklist) -> ChecklistOut:
    items = sorted(checklist.items, key=lambda i: i.sort_order)
    return ChecklistOut(
        id=checklist.id,
        organization_id=checklist.organization_id,
        work_order_id=checklist.work_order_id,
        name=checklist.name,
        template_key=checklist.template_key,
        items=[ChecklistItemOut.model_validate(i) for i in items],
    )


@router.get("", response_model=list[ChecklistOut])
def list_checklists(
    user: CurrentUser,
    db: DbSession,
    work_order_id: UUID | None = Query(None),
) -> list[ChecklistOut]:
    filters = [Checklist.organization_id == user.organization_id]
    if work_order_id is not None:
        filters.append(Checklist.work_order_id == work_order_id)

    rows = db.scalars(select(Checklist).where(*filters).order_by(Checklist.name)).all()
    # Ensure items are loaded
    result: list[ChecklistOut] = []
    for row in rows:
        _ = row.items
        result.append(_to_out(row))
    return result


@router.post("", response_model=ChecklistOut, status_code=201)
def create_checklist(
    body: ChecklistCreate, user: CurrentUser, db: DbSession
) -> ChecklistOut:
    _ensure_work_order(db, user, body.work_order_id)
    checklist = Checklist(
        organization_id=user.organization_id,
        work_order_id=body.work_order_id,
        name=body.name.strip(),
        template_key=body.template_key,
    )
    db.add(checklist)
    db.flush()
    for idx, label in enumerate(body.items):
        db.add(
            ChecklistItem(
                organization_id=user.organization_id,
                checklist_id=checklist.id,
                label=label.strip(),
                sort_order=idx,
            )
        )
    db.commit()
    db.refresh(checklist)
    _ = checklist.items
    return _to_out(checklist)


@router.patch("/items/{item_id}", response_model=ChecklistItemOut)
def update_checklist_item(
    item_id: UUID,
    body: ChecklistItemUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ChecklistItemOut:
    item = db.scalar(
        select(ChecklistItem).where(
            ChecklistItem.id == item_id,
            ChecklistItem.organization_id == user.organization_id,
        )
    )
    if item is None:
        raise not_found("Checklist item")

    # M5: optimistic concurrency — never silent overwrite
    if not _same_instant(item.updated_at, body.base_updated_at):
        raise conflict(
            "Checklist item was modified by another client",
            details={"server": ChecklistItemOut.model_validate(item).model_dump(mode="json")},
        )

    item.is_completed = body.is_completed
    item.completed_at = (
        datetime.now(tz=timezone.utc) if body.is_completed else None
    )
    checklist = db.get(Checklist, item.checklist_id)
    if checklist is not None:
        db.add(
            JobActivity(
                organization_id=user.organization_id,
                work_order_id=checklist.work_order_id,
                actor_user_id=user.id,
                activity_type=JobActivityType.CHECKLIST.value,
                note=(
                    f"Checklist item '{item.label}' marked "
                    f"{'complete' if body.is_completed else 'incomplete'}"
                ),
            )
        )
    db.commit()
    db.refresh(item)
    return ChecklistItemOut.model_validate(item)

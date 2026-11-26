"""Parts used on work orders."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import not_found
from app.models import PartUsed, WorkOrder
from app.schemas.parts import PartUsedCreate, PartUsedOut

router = APIRouter()


def _to_out(row: PartUsed) -> PartUsedOut:
    line_total: Decimal | None = None
    if row.unit_cost is not None:
        line_total = (row.unit_cost * row.quantity).quantize(Decimal("0.01"))
    return PartUsedOut(
        id=row.id,
        organization_id=row.organization_id,
        work_order_id=row.work_order_id,
        part_name=row.part_name,
        quantity=row.quantity,
        unit_cost=row.unit_cost,
        notes=row.notes,
        line_total=line_total,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[PartUsedOut])
def list_parts_used(
    user: CurrentUser,
    db: DbSession,
    work_order_id: UUID | None = Query(None),
) -> list[PartUsedOut]:
    filters = [PartUsed.organization_id == user.organization_id]
    if work_order_id is not None:
        filters.append(PartUsed.work_order_id == work_order_id)
    rows = db.scalars(
        select(PartUsed).where(*filters).order_by(PartUsed.created_at.desc())
    ).all()
    return [_to_out(r) for r in rows]


@router.post("", response_model=PartUsedOut, status_code=201)
def create_part_used(
    body: PartUsedCreate, user: CurrentUser, db: DbSession
) -> PartUsedOut:
    wo = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == body.work_order_id,
            WorkOrder.organization_id == user.organization_id,
            WorkOrder.archived_at.is_(None),
        )
    )
    if wo is None:
        raise not_found("Work order")
    row = PartUsed(
        organization_id=user.organization_id,
        work_order_id=body.work_order_id,
        part_name=body.part_name.strip(),
        quantity=body.quantity,
        unit_cost=body.unit_cost,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)

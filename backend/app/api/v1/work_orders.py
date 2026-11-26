"""Work orders — Milestone 1 org-scoped read for seed/smoke tests."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import WorkOrder
from app.schemas.common import Page, PageMeta, WorkOrderSummary

router = APIRouter()


@router.get("", response_model=Page[WorkOrderSummary])
def list_work_orders(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    status: str | None = Query(None),
) -> Page[WorkOrderSummary]:
    """List work orders for the caller's organization only."""
    filters = [
        WorkOrder.organization_id == user.organization_id,
        WorkOrder.archived_at.is_(None),
    ]
    if status:
        filters.append(WorkOrder.status == status)

    total = db.scalar(select(func.count()).select_from(WorkOrder).where(*filters)) or 0
    rows = db.scalars(
        select(WorkOrder)
        .where(*filters)
        .order_by(WorkOrder.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return Page(
        items=[
            WorkOrderSummary(
                id=row.id,
                organization_id=row.organization_id,
                title=row.title,
                status=row.status,
                priority=row.priority,
                customer_id=row.customer_id,
            )
            for row in rows
        ],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )

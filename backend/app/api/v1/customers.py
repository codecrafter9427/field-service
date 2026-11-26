"""Customers — Milestone 1 org-scoped read for seed/smoke tests."""

from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Customer
from app.schemas.common import CustomerSummary, Page, PageMeta

router = APIRouter()


@router.get("", response_model=Page[CustomerSummary])
def list_customers(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
) -> Page[CustomerSummary]:
    """List customers for the caller's organization only."""
    filters = [
        Customer.organization_id == user.organization_id,
        Customer.archived_at.is_(None),
    ]
    if search:
        like = f"%{search.strip()}%"
        filters.append(Customer.name.ilike(like))

    total = db.scalar(select(func.count()).select_from(Customer).where(*filters)) or 0
    rows = db.scalars(
        select(Customer)
        .where(*filters)
        .order_by(Customer.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return Page(
        items=[
            CustomerSummary(
                id=row.id,
                organization_id=row.organization_id,
                name=row.name,
                email=row.email,
                phone=row.phone,
            )
            for row in rows
        ],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )

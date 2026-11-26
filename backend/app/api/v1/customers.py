"""Customers — org-scoped CRUD."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import not_found
from app.models import Customer
from app.schemas.common import Page, PageMeta
from app.schemas.customers import (
    CustomerCreate,
    CustomerOut,
    CustomerUpdate,
)

router = APIRouter()


def _get_customer(db: DbSession, user: CurrentUser, customer_id: UUID) -> Customer:
    row = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == user.organization_id,
            Customer.archived_at.is_(None),
        )
    )
    if row is None:
        raise not_found("Customer")
    return row


@router.get("", response_model=Page[CustomerOut])
def list_customers(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    search: str | None = Query(None),
) -> Page[CustomerOut]:
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
        items=[CustomerOut.model_validate(row) for row in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    body: CustomerCreate, user: CurrentUser, db: DbSession
) -> CustomerOut:
    row = Customer(
        organization_id=user.organization_id,
        name=body.name.strip(),
        email=str(body.email) if body.email else None,
        phone=body.phone,
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CustomerOut.model_validate(row)


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: UUID, user: CurrentUser, db: DbSession
) -> CustomerOut:
    return CustomerOut.model_validate(_get_customer(db, user, customer_id))


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: UUID,
    body: CustomerUpdate,
    user: CurrentUser,
    db: DbSession,
) -> CustomerOut:
    row = _get_customer(db, user, customer_id)
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return CustomerOut.model_validate(row)


@router.delete("/{customer_id}", status_code=204)
def archive_customer(
    customer_id: UUID, user: CurrentUser, db: DbSession
) -> None:
    row = _get_customer(db, user, customer_id)
    row.archived_at = datetime.now(tz=timezone.utc)
    db.commit()

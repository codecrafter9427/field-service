"""Service locations — org-scoped CRUD."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import bad_request, not_found
from app.models import Customer, ServiceLocation
from app.schemas.common import Page, PageMeta
from app.schemas.customers import (
    ServiceLocationCreate,
    ServiceLocationOut,
    ServiceLocationUpdate,
)

router = APIRouter()


def _get_location(
    db: DbSession, user: CurrentUser, location_id: UUID
) -> ServiceLocation:
    row = db.scalar(
        select(ServiceLocation).where(
            ServiceLocation.id == location_id,
            ServiceLocation.organization_id == user.organization_id,
            ServiceLocation.archived_at.is_(None),
        )
    )
    if row is None:
        raise not_found("Service location")
    return row


def _ensure_customer(db: DbSession, user: CurrentUser, customer_id: UUID) -> Customer:
    row = db.scalar(
        select(Customer).where(
            Customer.id == customer_id,
            Customer.organization_id == user.organization_id,
            Customer.archived_at.is_(None),
        )
    )
    if row is None:
        raise bad_request("invalid_customer", "Customer not found in your organization")
    return row


@router.get("", response_model=Page[ServiceLocationOut])
def list_service_locations(
    user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    customer_id: UUID | None = Query(None),
) -> Page[ServiceLocationOut]:
    filters = [
        ServiceLocation.organization_id == user.organization_id,
        ServiceLocation.archived_at.is_(None),
    ]
    if customer_id is not None:
        filters.append(ServiceLocation.customer_id == customer_id)

    total = (
        db.scalar(select(func.count()).select_from(ServiceLocation).where(*filters))
        or 0
    )
    rows = db.scalars(
        select(ServiceLocation)
        .where(*filters)
        .order_by(ServiceLocation.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return Page(
        items=[ServiceLocationOut.model_validate(row) for row in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.post("", response_model=ServiceLocationOut, status_code=201)
def create_service_location(
    body: ServiceLocationCreate, user: CurrentUser, db: DbSession
) -> ServiceLocationOut:
    _ensure_customer(db, user, body.customer_id)
    row = ServiceLocation(
        organization_id=user.organization_id,
        customer_id=body.customer_id,
        name=body.name.strip(),
        address_line1=body.address_line1,
        address_line2=body.address_line2,
        city=body.city,
        region=body.region,
        postal_code=body.postal_code,
        country=body.country.upper(),
        notes=body.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return ServiceLocationOut.model_validate(row)


@router.get("/{location_id}", response_model=ServiceLocationOut)
def get_service_location(
    location_id: UUID, user: CurrentUser, db: DbSession
) -> ServiceLocationOut:
    return ServiceLocationOut.model_validate(_get_location(db, user, location_id))


@router.patch("/{location_id}", response_model=ServiceLocationOut)
def update_service_location(
    location_id: UUID,
    body: ServiceLocationUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ServiceLocationOut:
    row = _get_location(db, user, location_id)
    data = body.model_dump(exclude_unset=True)
    if "country" in data and data["country"] is not None:
        data["country"] = data["country"].upper()
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return ServiceLocationOut.model_validate(row)


@router.delete("/{location_id}", status_code=204)
def archive_service_location(
    location_id: UUID, user: CurrentUser, db: DbSession
) -> None:
    row = _get_location(db, user, location_id)
    row.archived_at = datetime.now(tz=timezone.utc)
    db.commit()

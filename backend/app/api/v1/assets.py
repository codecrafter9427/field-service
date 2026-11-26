"""Assets — org-scoped CRUD + service history."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, or_, select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import bad_request, not_found
from app.models import Asset, Customer, ServiceLocation
from app.schemas.assets import (
    AssetCreate,
    AssetOut,
    AssetUpdate,
    ServiceHistoryItem,
)
from app.schemas.common import Page, PageMeta
from app.services.history import service_history

router = APIRouter()


def _get_asset(db: DbSession, user: CurrentUser, asset_id: UUID) -> Asset:
    asset = db.scalar(
        select(Asset).where(
            Asset.id == asset_id,
            Asset.organization_id == user.organization_id,
            Asset.archived_at.is_(None),
        )
    )
    if asset is None:
        raise not_found("Asset")
    return asset


def _ensure_customer(db: DbSession, org_id: UUID, customer_id: UUID) -> None:
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
    db: DbSession, org_id: UUID, location_id: UUID | None, customer_id: UUID
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


@router.get("", response_model=Page[AssetOut])
def list_assets(
    db: DbSession,
    user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    customer_id: UUID | None = None,
    q: str | None = None,
) -> Page[AssetOut]:
    stmt = select(Asset).where(
        Asset.organization_id == user.organization_id,
        Asset.archived_at.is_(None),
    )
    if customer_id is not None:
        stmt = stmt.where(Asset.customer_id == customer_id)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Asset.name.ilike(like),
                Asset.serial_number.ilike(like),
                Asset.asset_type.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Asset.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[AssetOut.model_validate(a) for a in rows],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(body: AssetCreate, db: DbSession, user: CurrentUser) -> AssetOut:
    _ensure_customer(db, user.organization_id, body.customer_id)
    _ensure_location(
        db, user.organization_id, body.service_location_id, body.customer_id
    )
    row = Asset(
        organization_id=user.organization_id,
        customer_id=body.customer_id,
        service_location_id=body.service_location_id,
        name=body.name.strip(),
        serial_number=body.serial_number,
        asset_type=body.asset_type,
        manufacturer=body.manufacturer,
        model_number=body.model_number,
        warranty_expires_on=body.warranty_expires_on,
        maintenance_notes=body.maintenance_notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return AssetOut.model_validate(row)


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: UUID, db: DbSession, user: CurrentUser) -> AssetOut:
    return AssetOut.model_validate(_get_asset(db, user, asset_id))


@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: UUID, body: AssetUpdate, db: DbSession, user: CurrentUser
) -> AssetOut:
    row = _get_asset(db, user, asset_id)
    data = body.model_dump(exclude_unset=True)
    if "service_location_id" in data:
        _ensure_location(
            db, user.organization_id, data["service_location_id"], row.customer_id
        )
    if "name" in data and data["name"] is not None:
        data["name"] = data["name"].strip()
    for key, value in data.items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return AssetOut.model_validate(row)


@router.delete("/{asset_id}", status_code=204)
def archive_asset(asset_id: UUID, db: DbSession, user: CurrentUser) -> None:
    row = _get_asset(db, user, asset_id)
    row.archived_at = datetime.now(timezone.utc)
    db.commit()


@router.get("/{asset_id}/service-history", response_model=list[ServiceHistoryItem])
def asset_service_history(
    asset_id: UUID, db: DbSession, user: CurrentUser
) -> list[ServiceHistoryItem]:
    asset = _get_asset(db, user, asset_id)
    return service_history(
        db, organization_id=user.organization_id, asset_id=asset.id
    )

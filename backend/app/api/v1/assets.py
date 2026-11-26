"""Assets — org-scoped read list for Service Memory / job prep (write CRUD still later)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import not_found
from app.models import Asset
from app.schemas.common import Page, PageMeta

router = APIRouter()


class AssetOut(BaseModel):
    id: UUID
    organization_id: UUID
    customer_id: UUID
    service_location_id: UUID | None = None
    name: str
    serial_number: str | None = None
    asset_type: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    maintenance_notes: str | None = None


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
        stmt = stmt.where(Asset.name.ilike(like))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Asset.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[
            AssetOut(
                id=a.id,
                organization_id=a.organization_id,
                customer_id=a.customer_id,
                service_location_id=a.service_location_id,
                name=a.name,
                serial_number=a.serial_number,
                asset_type=a.asset_type,
                manufacturer=a.manufacturer,
                model_number=a.model_number,
                maintenance_notes=a.maintenance_notes,
            )
            for a in rows
        ],
        meta=PageMeta(page=page, page_size=page_size, total=total),
    )


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: UUID, db: DbSession, user: CurrentUser) -> AssetOut:
    asset = db.get(Asset, asset_id)
    if asset is None or asset.archived_at is not None:
        raise not_found("Asset")
    if asset.organization_id != user.organization_id:
        raise not_found("Asset")
    return AssetOut(
        id=asset.id,
        organization_id=asset.organization_id,
        customer_id=asset.customer_id,
        service_location_id=asset.service_location_id,
        name=asset.name,
        serial_number=asset.serial_number,
        asset_type=asset.asset_type,
        manufacturer=asset.manufacturer,
        model_number=asset.model_number,
        maintenance_notes=asset.maintenance_notes,
    )

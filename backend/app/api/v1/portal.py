"""Customer portal links (staff) + public redacted job-status."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.deps import DbSession, DispatcherUser
from app.api.errors import not_found
from app.core.config import settings
from app.core.rate_limit import check_rate_limit, client_ip
from app.core.security import generate_portal_token, hash_portal_token
from app.models import AuditEvent, WorkOrder
from app.models.portal import CustomerPortalLink
from app.schemas.portal import (
    CustomerJobStatusOut,
    PortalLinkCreate,
    PortalLinkCreated,
    PortalLinkOut,
)
from app.services.portal_status import build_customer_job_status

router = APIRouter()


def _link_out(link: CustomerPortalLink, *, now: datetime | None = None) -> PortalLinkOut:
    now = now or datetime.now(timezone.utc)
    active = link.revoked_at is None and link.expires_at > now
    return PortalLinkOut(
        id=link.id,
        work_order_id=link.work_order_id,
        expires_at=link.expires_at,
        revoked_at=link.revoked_at,
        created_by_id=link.created_by_id,
        created_at=link.created_at,
        last_accessed_at=link.last_accessed_at,
        is_active=active,
    )


def _get_work_order(db: DbSession, organization_id: UUID, work_order_id: UUID) -> WorkOrder:
    wo = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.organization_id == organization_id,
            WorkOrder.archived_at.is_(None),
        )
    )
    if wo is None:
        raise not_found("Work order")
    return wo


@router.post(
    "/work-orders/{work_order_id}/portal-links",
    response_model=PortalLinkCreated,
)
def create_portal_link(
    work_order_id: UUID,
    body: PortalLinkCreate,
    user: DispatcherUser,
    db: DbSession,
) -> PortalLinkCreated:
    wo = _get_work_order(db, user.organization_id, work_order_id)
    hours = body.expire_hours or settings.portal_link_expire_hours
    raw = generate_portal_token()
    now = datetime.now(timezone.utc)
    link = CustomerPortalLink(
        organization_id=user.organization_id,
        work_order_id=wo.id,
        token_hash=hash_portal_token(raw),
        expires_at=now + timedelta(hours=hours),
        created_by_id=user.id,
    )
    db.add(link)
    db.flush()
    db.add(
        AuditEvent(
            organization_id=user.organization_id,
            actor_user_id=user.id,
            entity_type="customer_portal_link",
            entity_id=link.id,
            action="portal_link.create",
            payload={"work_order_id": str(wo.id), "expires_at": link.expires_at.isoformat()},
        )
    )
    db.commit()
    db.refresh(link)

    return PortalLinkCreated(
        id=link.id,
        work_order_id=wo.id,
        url_path=f"/status/{raw}",
        raw_token=raw,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )


@router.get(
    "/work-orders/{work_order_id}/portal-links",
    response_model=list[PortalLinkOut],
)
def list_portal_links(
    work_order_id: UUID,
    user: DispatcherUser,
    db: DbSession,
) -> list[PortalLinkOut]:
    _get_work_order(db, user.organization_id, work_order_id)
    links = db.scalars(
        select(CustomerPortalLink)
        .where(
            CustomerPortalLink.work_order_id == work_order_id,
            CustomerPortalLink.organization_id == user.organization_id,
        )
        .order_by(CustomerPortalLink.created_at.desc())
    ).all()
    now = datetime.now(timezone.utc)
    return [_link_out(link, now=now) for link in links]


@router.post("/portal-links/{link_id}/revoke", response_model=PortalLinkOut)
def revoke_portal_link(
    link_id: UUID,
    user: DispatcherUser,
    db: DbSession,
) -> PortalLinkOut:
    link = db.scalar(
        select(CustomerPortalLink).where(
            CustomerPortalLink.id == link_id,
            CustomerPortalLink.organization_id == user.organization_id,
        )
    )
    if link is None:
        raise not_found("Portal link")
    if link.revoked_at is None:
        link.revoked_at = datetime.now(timezone.utc)
        db.add(
            AuditEvent(
                organization_id=user.organization_id,
                actor_user_id=user.id,
                entity_type="customer_portal_link",
                entity_id=link.id,
                action="portal_link.revoke",
                payload={"work_order_id": str(link.work_order_id)},
            )
        )
        db.commit()
        db.refresh(link)
    return _link_out(link)


@router.get("/public/job-status", response_model=CustomerJobStatusOut)
def public_job_status(
    token: str,
    request: Request,
    db: DbSession,
) -> CustomerJobStatusOut:
    check_rate_limit(
        f"portal:{client_ip(request)}",
        limit=settings.rate_limit_portal_per_minute,
    )
    if not token or len(token) < 16:
        raise not_found("Job status link")

    token_hash = hash_portal_token(token)
    link = db.scalar(
        select(CustomerPortalLink).where(CustomerPortalLink.token_hash == token_hash)
    )
    now = datetime.now(timezone.utc)

    def _deny(*, org_id: UUID, link_id: UUID | None, reason: str) -> None:
        db.add(
            AuditEvent(
                organization_id=org_id,
                actor_user_id=None,
                entity_type="customer_portal_link",
                entity_id=link_id,
                action="portal_link.access_denied",
                payload={"reason": reason},
            )
        )
        db.commit()
        raise not_found("Job status link")

    if link is None:
        raise not_found("Job status link")
    if link.revoked_at is not None:
        _deny(org_id=link.organization_id, link_id=link.id, reason="revoked")
    if link.expires_at <= now:
        _deny(org_id=link.organization_id, link_id=link.id, reason="expired")

    wo = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == link.work_order_id,
            WorkOrder.organization_id == link.organization_id,
            WorkOrder.archived_at.is_(None),
        )
    )
    if wo is None:
        _deny(org_id=link.organization_id, link_id=link.id, reason="work_order_missing")

    link.last_accessed_at = now
    db.commit()
    db.refresh(link)
    assert wo is not None
    return build_customer_job_status(db, link, wo)

"""Customer acknowledgement signoff — not certified e-signature."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import not_found
from app.models import AuditEvent, CustomerSignoff, JobActivity, WorkOrder
from app.models.enums import JobActivityType
from app.schemas.signoffs import SignoffCreate, SignoffOut

router = APIRouter()


def _get_work_order(db: DbSession, user: CurrentUser, work_order_id: UUID) -> WorkOrder:
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


def _to_out(row: CustomerSignoff) -> SignoffOut:
    return SignoffOut(
        id=row.id,
        organization_id=row.organization_id,
        work_order_id=row.work_order_id,
        signer_name=row.signer_name,
        signed_at=row.signed_at,
        acknowledgement_text=row.acknowledgement_text,
        signature_storage_key=row.signature_storage_key,
        is_certified_esignature=False,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/work-orders/{work_order_id}/signoffs", response_model=list[SignoffOut])
def list_signoffs(
    work_order_id: UUID, db: DbSession, user: CurrentUser
) -> list[SignoffOut]:
    _get_work_order(db, user, work_order_id)
    rows = db.scalars(
        select(CustomerSignoff)
        .where(
            CustomerSignoff.work_order_id == work_order_id,
            CustomerSignoff.organization_id == user.organization_id,
        )
        .order_by(CustomerSignoff.signed_at.desc())
    ).all()
    return [_to_out(r) for r in rows]


@router.post(
    "/work-orders/{work_order_id}/signoffs",
    response_model=SignoffOut,
    status_code=201,
)
def create_signoff(
    work_order_id: UUID,
    body: SignoffCreate,
    db: DbSession,
    user: CurrentUser,
) -> SignoffOut:
    """Record timestamped customer acknowledgement (not certified e-sign)."""
    wo = _get_work_order(db, user, work_order_id)
    now = datetime.now(timezone.utc)
    storage_key: str | None = None
    if body.signature_data_url:
        # Demo stub: persist a short metadata key, not a certified signature blob store
        storage_key = f"demo/signoffs/{work_order_id}/{uuid4()}.png"
        if body.signature_data_url.startswith("data:"):
            storage_key = f"{storage_key}#data-url-stub"

    row = CustomerSignoff(
        organization_id=user.organization_id,
        work_order_id=wo.id,
        signer_name=body.signer_name.strip(),
        signed_at=now,
        acknowledgement_text=body.acknowledgement_text.strip(),
        signature_storage_key=storage_key,
    )
    db.add(row)
    db.flush()
    db.add(
        JobActivity(
            organization_id=user.organization_id,
            work_order_id=wo.id,
            actor_user_id=user.id,
            activity_type=JobActivityType.SIGNOFF.value,
            note=(
                f"Customer acknowledgement by {row.signer_name} "
                f"(not a certified e-signature) at {now.isoformat()}"
            ),
            occurred_at=now,
        )
    )
    db.add(
        AuditEvent(
            organization_id=user.organization_id,
            actor_user_id=user.id,
            entity_type="customer_signoff",
            entity_id=row.id,
            action="create_acknowledgement",
            payload={
                "work_order_id": str(wo.id),
                "signer_name": row.signer_name,
                "signed_at": now.isoformat(),
                "certified_esignature": False,
            },
        )
    )
    db.commit()
    db.refresh(row)
    return _to_out(row)

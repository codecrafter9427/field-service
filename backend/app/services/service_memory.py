"""Service Memory — retrieve recurring failure history by asset/customer (org-scoped)."""

from __future__ import annotations

from collections import Counter
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import Asset, Customer, JobActivity, WorkOrder
from app.models.enums import JobActivityType
from app.schemas.ai import ServiceMemoryHit
from app.schemas.common import AISource


# Phrases that help surface recurring themes from seeded / recorded notes.
THEME_KEYWORDS = (
    "filter",
    "clog",
    "leak",
    "refrigerant",
    "vibration",
    "seal",
    "gasket",
    "overheat",
    "noise",
    "drain",
    "coil",
    "intermittent",
    "timeout",
    "frost",
)


def search_service_history(
    db: Session,
    *,
    organization_id: UUID,
    query: str = "",
    asset_id: UUID | None = None,
    customer_id: UUID | None = None,
    limit: int = 20,
) -> tuple[list[ServiceMemoryHit], list[AISource], list[str]]:
    """
    Search recorded work-order history for recurring issues.

    Returns hits, source refs, and raw note texts for AI summarization.
    """
    stmt = (
        select(WorkOrder, JobActivity, Asset, Customer)
        .join(JobActivity, JobActivity.work_order_id == WorkOrder.id)
        .outerjoin(Asset, Asset.id == WorkOrder.asset_id)
        .join(Customer, Customer.id == WorkOrder.customer_id)
        .where(
            WorkOrder.organization_id == organization_id,
            WorkOrder.archived_at.is_(None),
            JobActivity.activity_type.in_(
                [JobActivityType.NOTE.value, JobActivityType.STATUS_CHANGE.value]
            ),
        )
        .order_by(JobActivity.occurred_at.desc())
    )
    if asset_id is not None:
        stmt = stmt.where(WorkOrder.asset_id == asset_id)
    if customer_id is not None:
        stmt = stmt.where(WorkOrder.customer_id == customer_id)

    q = (query or "").strip().lower()
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                WorkOrder.title.ilike(like),
                WorkOrder.description.ilike(like),
                JobActivity.note.ilike(like),
                Asset.name.ilike(like),
                Asset.maintenance_notes.ilike(like),
            )
        )

    rows = db.execute(stmt.limit(limit * 3)).all()

    hits: list[ServiceMemoryHit] = []
    sources: list[AISource] = []
    note_texts: list[str] = []
    seen_wo: set[UUID] = set()

    for wo, activity, asset, customer in rows:
        note = activity.note or ""
        note_texts.append(f"{wo.title}: {note}")
        if wo.id in seen_wo and len(hits) >= limit:
            continue
        if wo.id not in seen_wo:
            seen_wo.add(wo.id)
            hits.append(
                ServiceMemoryHit(
                    work_order_id=wo.id,
                    title=wo.title,
                    status=wo.status,
                    customer_id=wo.customer_id,
                    customer_name=customer.name if customer else None,
                    asset_id=wo.asset_id,
                    asset_name=asset.name if asset else None,
                    note_excerpt=(note[:240] if note else None),
                    occurred_at=activity.occurred_at.isoformat() if activity.occurred_at else None,
                )
            )
            sources.append(
                AISource(
                    type="work_order",
                    id=str(wo.id),
                    label=wo.title,
                )
            )
        if len(hits) >= limit:
            break

    return hits, sources, note_texts


def extract_theme_counts(note_texts: list[str], titles: list[str]) -> Counter[str]:
    counter: Counter[str] = Counter()
    blob_parts = [*(n.lower() for n in note_texts), *(t.lower() for t in titles)]
    for text in blob_parts:
        for kw in THEME_KEYWORDS:
            if kw in text:
                counter[kw] += 1
    return counter


def build_recurring_context(
    hits: list[ServiceMemoryHit],
    note_texts: list[str],
) -> dict:
    titles = [h.title for h in hits]
    themes = extract_theme_counts(note_texts, titles)
    asset_names = sorted({h.asset_name for h in hits if h.asset_name})
    customer_names = sorted({h.customer_name for h in hits if h.customer_name})
    return {
        "hit_count": len(hits),
        "asset_names": asset_names,
        "customer_names": customer_names,
        "theme_counts": dict(themes.most_common(8)),
        "titles": titles[:12],
        "notes_sample": note_texts[:12],
    }

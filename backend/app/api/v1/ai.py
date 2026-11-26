"""AI endpoints — service report, job prep, Service Memory (org-scoped, confirm-gated)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.ai import get_ai_provider
from app.api.deps import CurrentUser, DbSession
from app.api.errors import bad_request, not_found
from app.models import (
    Asset,
    Attachment,
    AuditEvent,
    Checklist,
    ChecklistItem,
    Customer,
    JobActivity,
    PartUsed,
    WorkOrder,
)
from app.models.enums import JobActivityType
from app.schemas.ai import (
    ConfirmChecklistRequest,
    ConfirmChecklistResponse,
    JobPrepRequest,
    JobPrepResponse,
    ChecklistSuggestion,
    ServiceMemoryResponse,
    ServiceMemorySearchRequest,
    ServiceReportApproveRequest,
    ServiceReportApproveResponse,
    ServiceReportDraftRequest,
    ServiceReportDraftResponse,
    ServiceReportSection,
)
from app.schemas.common import AISource
from app.services.checklist_templates import resolve_job_type
from app.services.service_memory import build_recurring_context, search_service_history

router = APIRouter()


def _get_org_work_order(db: DbSession, user: CurrentUser, work_order_id: UUID) -> WorkOrder:
    wo = db.get(WorkOrder, work_order_id)
    if wo is None or wo.archived_at is not None:
        raise not_found("Work order")
    if wo.organization_id != user.organization_id:
        raise not_found("Work order")
    return wo


@router.post("/service-report", response_model=ServiceReportDraftResponse)
async def draft_service_report(
    body: ServiceReportDraftRequest,
    db: DbSession,
    user: CurrentUser,
) -> ServiceReportDraftResponse:
    """Turn technician notes into an editable structured report draft. AI cannot complete/sign."""
    wo = _get_org_work_order(db, user, body.work_order_id)
    asset = db.get(Asset, wo.asset_id) if wo.asset_id else None

    notes_rows = db.scalars(
        select(JobActivity)
        .where(
            JobActivity.work_order_id == wo.id,
            JobActivity.organization_id == user.organization_id,
            JobActivity.activity_type == JobActivityType.NOTE.value,
        )
        .order_by(JobActivity.occurred_at.desc())
    ).all()
    stored_notes = "\n".join(a.note for a in notes_rows if a.note)
    input_text = "\n".join(
        p for p in (body.notes, body.transcript, stored_notes) if p and p.strip()
    ).strip()

    parts = db.scalars(
        select(PartUsed).where(
            PartUsed.work_order_id == wo.id,
            PartUsed.organization_id == user.organization_id,
        )
    ).all()
    parts_used = [f"{p.part_name} x{p.quantity}" for p in parts]

    provider = get_ai_provider()
    raw = await provider.generate_structured(
        task="service_report",
        input_text=input_text or wo.description or wo.title,
        context={
            "work_order_id": str(wo.id),
            "title": wo.title,
            "description": wo.description,
            "asset_name": asset.name if asset else None,
            "asset_type": asset.asset_type if asset else None,
            "parts_used": parts_used,
            "status": wo.status,
        },
    )

    draft = ServiceReportSection(
        problem=str(raw.get("problem") or ""),
        diagnosis=str(raw.get("diagnosis") or ""),
        work_performed=str(raw.get("work_performed") or ""),
        parts=[str(p) for p in (raw.get("parts") or [])],
        follow_up=str(raw.get("follow_up") or ""),
    )
    sources = [
        AISource(type="work_order", id=str(wo.id), label=wo.title),
    ]
    for activity in notes_rows[:5]:
        sources.append(
            AISource(
                type="job_activity",
                id=str(activity.id),
                label=(activity.note or "note")[:80],
            )
        )

    return ServiceReportDraftResponse(
        work_order_id=wo.id,
        draft=draft,
        explanation=(
            "AI-generated draft labeled for review. Technician must edit/approve before final. "
            "AI cannot complete the job, certify safety, or sign for the customer."
        ),
        sources=sources,
        requires_confirmation=True,
        provider=str(raw.get("provider") or "demo"),
    )


@router.post("/service-report/approve", response_model=ServiceReportApproveResponse)
async def approve_service_report(
    body: ServiceReportApproveRequest,
    db: DbSession,
    user: CurrentUser,
) -> ServiceReportApproveResponse:
    """Persist an edited AI report as attachment metadata + audit. Does not complete or sign."""
    wo = _get_org_work_order(db, user, body.work_order_id)
    if not body.edited:
        raise bad_request(
            "confirmation_required",
            "Report must be reviewed/edited (edited=true) before approval",
        )
    if not (body.problem.strip() and body.work_performed.strip()):
        raise bad_request(
            "invalid_report",
            "Approved report requires problem and work_performed",
        )

    now = datetime.now(tz=timezone.utc)
    payload = {
        "problem": body.problem.strip(),
        "diagnosis": body.diagnosis.strip(),
        "work_performed": body.work_performed.strip(),
        "parts": body.parts,
        "follow_up": body.follow_up.strip(),
        "approved_by": str(user.id),
        "approved_at": now.isoformat(),
        "ai_labeled": True,
        "job_completed_by_ai": False,
        "signed_by_ai": False,
    }

    attachment = Attachment(
        organization_id=user.organization_id,
        work_order_id=wo.id,
        filename=f"service-report-{wo.id}.json",
        content_type="application/json",
        storage_key=f"demo/reports/service-report-{wo.id}-{int(now.timestamp())}.json",
        byte_size=len(str(payload)),
        uploaded_by_id=user.id,
    )
    db.add(attachment)
    db.flush()

    audit = AuditEvent(
        organization_id=user.organization_id,
        actor_user_id=user.id,
        entity_type="service_report",
        entity_id=wo.id,
        action="ai_report_approved",
        payload={**payload, "attachment_id": str(attachment.id)},
    )
    db.add(audit)
    db.add(
        JobActivity(
            organization_id=user.organization_id,
            work_order_id=wo.id,
            actor_user_id=user.id,
            activity_type=JobActivityType.NOTE.value,
            note=(
                "Approved AI service report draft (human-edited). "
                "Job status unchanged; customer signoff not created by AI."
            ),
            occurred_at=now,
        )
    )
    db.commit()
    db.refresh(attachment)
    db.refresh(audit)

    return ServiceReportApproveResponse(
        work_order_id=wo.id,
        approved=True,
        attachment_id=attachment.id,
        audit_event_id=audit.id,
        status_unchanged=wo.status,
        message=(
            "Report approved and stored as attachment metadata. "
            f"Work order status remains '{wo.status}'. AI did not complete or sign."
        ),
    )


@router.post("/job-prep", response_model=JobPrepResponse)
async def job_prep(
    body: JobPrepRequest,
    db: DbSession,
    user: CurrentUser,
) -> JobPrepResponse:
    """Summarize asset history/checklist and suggest checklist items by job type (confirm required)."""
    wo = _get_org_work_order(db, user, body.work_order_id)
    asset = db.get(Asset, wo.asset_id) if wo.asset_id else None

    history_highlights: list[str] = []
    sources: list[AISource] = [
        AISource(type="work_order", id=str(wo.id), label=wo.title),
    ]

    # Prior jobs on same asset (or customer if no asset)
    hist_stmt = select(WorkOrder).where(
        WorkOrder.organization_id == user.organization_id,
        WorkOrder.archived_at.is_(None),
        WorkOrder.id != wo.id,
    )
    if wo.asset_id:
        hist_stmt = hist_stmt.where(WorkOrder.asset_id == wo.asset_id)
    else:
        hist_stmt = hist_stmt.where(WorkOrder.customer_id == wo.customer_id)
    prior = db.scalars(hist_stmt.order_by(WorkOrder.updated_at.desc()).limit(8)).all()
    for prior_wo in prior:
        history_highlights.append(f"{prior_wo.title} [{prior_wo.status}]")
        sources.append(
            AISource(type="work_order", id=str(prior_wo.id), label=prior_wo.title)
        )

    history_ids = [p.id for p in prior] or [wo.id]
    note_rows = db.scalars(
        select(JobActivity)
        .where(
            JobActivity.organization_id == user.organization_id,
            JobActivity.work_order_id.in_(history_ids),
            JobActivity.activity_type == JobActivityType.NOTE.value,
        )
        .order_by(JobActivity.occurred_at.desc())
        .limit(10)
    ).all()
    for note in note_rows:
        if note.note:
            history_highlights.append(note.note[:160])

    if asset and asset.maintenance_notes:
        history_highlights.append(f"Asset maintenance notes: {asset.maintenance_notes}")
        sources.append(
            AISource(type="asset", id=str(asset.id), label=asset.name)
        )

    checklists = db.scalars(
        select(Checklist).where(
            Checklist.work_order_id == wo.id,
            Checklist.organization_id == user.organization_id,
        )
    ).all()
    existing_labels: list[str] = []
    for cl in checklists:
        items = db.scalars(
            select(ChecklistItem).where(ChecklistItem.checklist_id == cl.id)
        ).all()
        existing_labels.extend(i.label for i in items)
        sources.append(AISource(type="checklist", id=str(cl.id), label=cl.name))

    job_type = resolve_job_type(
        title=wo.title,
        skill_required=wo.skill_required,
        asset_type=asset.asset_type if asset else None,
        explicit=body.job_type,
    )

    provider = get_ai_provider()
    raw = await provider.generate_structured(
        task="job_prep",
        input_text=wo.title,
        context={
            "title": wo.title,
            "skill_required": wo.skill_required,
            "asset_name": asset.name if asset else None,
            "asset_type": asset.asset_type if asset else None,
            "job_type": job_type,
            "history_highlights": history_highlights,
            "existing_checklist": existing_labels,
        },
    )

    suggestions_raw = raw.get("suggested_checklist") or []
    suggestions: list[ChecklistSuggestion] = []
    for item in suggestions_raw:
        if isinstance(item, dict) and item.get("label"):
            suggestions.append(
                ChecklistSuggestion(
                    label=str(item["label"]),
                    reason=str(item.get("reason") or "Suggested for job type"),
                    confirmed=False,
                )
            )

    return JobPrepResponse(
        work_order_id=wo.id,
        summary=str(raw.get("summary") or ""),
        history_highlights=list(raw.get("history_highlights") or history_highlights),
        existing_checklist=existing_labels,
        suggested_checklist=suggestions,
        explanation=(
            f"Job prep for type '{job_type}'. Suggested checklist items require technician "
            "confirmation before they are added. AI cannot complete the job."
        ),
        sources=sources,
        requires_confirmation=True,
        provider=str(raw.get("provider") or "demo"),
    )


@router.post("/job-prep/confirm-checklist", response_model=ConfirmChecklistResponse)
async def confirm_checklist_suggestions(
    body: ConfirmChecklistRequest,
    db: DbSession,
    user: CurrentUser,
) -> ConfirmChecklistResponse:
    """Add technician-confirmed checklist suggestions to the work order."""
    wo = _get_org_work_order(db, user, body.work_order_id)
    labels = [lab.strip() for lab in body.items if lab and lab.strip()]
    if not labels:
        raise bad_request(
            "confirmation_required",
            "At least one confirmed checklist item is required",
        )

    checklist = db.scalar(
        select(Checklist)
        .where(
            Checklist.work_order_id == wo.id,
            Checklist.organization_id == user.organization_id,
        )
        .order_by(Checklist.created_at.asc())
        .limit(1)
    )
    if checklist is None:
        checklist = Checklist(
            organization_id=user.organization_id,
            work_order_id=wo.id,
            name="AI-suggested checklist (confirmed)",
            template_key="ai_confirmed",
        )
        db.add(checklist)
        db.flush()

    existing = {
        i.label
        for i in db.scalars(
            select(ChecklistItem).where(ChecklistItem.checklist_id == checklist.id)
        ).all()
    }
    max_order = db.scalar(
        select(ChecklistItem.sort_order)
        .where(ChecklistItem.checklist_id == checklist.id)
        .order_by(ChecklistItem.sort_order.desc())
        .limit(1)
    )
    sort_base = (max_order or 0) + 1
    added: list[str] = []
    for offset, label in enumerate(labels):
        if label in existing:
            continue
        db.add(
            ChecklistItem(
                organization_id=user.organization_id,
                checklist_id=checklist.id,
                label=label,
                is_required=False,
                is_completed=False,
                sort_order=sort_base + offset,
            )
        )
        added.append(label)
        existing.add(label)

    db.add(
        AuditEvent(
            organization_id=user.organization_id,
            actor_user_id=user.id,
            entity_type="checklist",
            entity_id=checklist.id,
            action="ai_checklist_confirmed",
            payload={"work_order_id": str(wo.id), "added": added},
        )
    )
    db.commit()

    return ConfirmChecklistResponse(
        work_order_id=wo.id,
        checklist_id=checklist.id,
        added_labels=added,
        message=(
            f"Added {len(added)} confirmed checklist item(s). "
            "Unconfirmed AI suggestions were not applied."
        ),
    )


@router.post("/service-memory", response_model=ServiceMemoryResponse)
async def service_memory(
    body: ServiceMemorySearchRequest,
    db: DbSession,
    user: CurrentUser,
) -> ServiceMemoryResponse:
    """Differentiator: search recurring failures by asset/customer; AI summarizes recorded history."""
    if body.asset_id is not None:
        asset = db.get(Asset, body.asset_id)
        if asset is None or asset.organization_id != user.organization_id:
            raise not_found("Asset")
    if body.customer_id is not None:
        customer = db.get(Customer, body.customer_id)
        if customer is None or customer.organization_id != user.organization_id:
            raise not_found("Customer")

    hits, sources, note_texts = search_service_history(
        db,
        organization_id=user.organization_id,
        query=body.query,
        asset_id=body.asset_id,
        customer_id=body.customer_id,
        limit=body.limit,
    )
    ctx = build_recurring_context(hits, note_texts)
    ctx["query"] = body.query

    provider = get_ai_provider()
    raw = await provider.generate_structured(
        task="service_memory",
        input_text=body.query or "recurring failures",
        context=ctx,
    )

    themes = [str(t) for t in (raw.get("recurring_themes") or [])]
    follow = str(raw.get("suggested_follow_up") or "")
    result = {
        "recurring_themes": themes,
        "suggested_follow_up": follow,
        "hit_count": len(hits),
        "provider": raw.get("provider"),
        "labeled_ai": True,
    }

    return ServiceMemoryResponse(
        query=body.query,
        recurring_themes=themes,
        suggested_follow_up=follow,
        hits=hits,
        explanation=(
            "Service Memory summary from recorded job history only. "
            "Sources listed below. Confirm before creating any follow-up work order."
        ),
        sources=sources,
        requires_confirmation=True,
        provider=str(raw.get("provider") or "demo"),
        result=result,
    )

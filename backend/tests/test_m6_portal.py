"""M6 customer portal — expiry, revoke, scope, redaction, tenant isolation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import hash_portal_token
from app.models import AuditEvent, WorkOrder
from app.models.portal import CustomerPortalLink
from scripts.seed import DEMO_PORTAL_RAW_TOKEN


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _first_wo_id(client: TestClient, token: str) -> str:
    res = client.get("/api/v1/work-orders?page_size=5", headers=_auth(token))
    assert res.status_code == 200, res.text
    items = res.json()["items"]
    assert items
    return items[0]["id"]


def test_dispatcher_creates_and_resolves_portal_link(client, dispatcher_token):
    wo_id = _first_wo_id(client, dispatcher_token)
    created = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={"expire_hours": 24},
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["raw_token"]
    assert body["url_path"].startswith("/status/")
    assert body["work_order_id"] == wo_id

    status = client.get(
        "/api/v1/public/job-status",
        params={"token": body["raw_token"]},
    )
    assert status.status_code == 200, status.text
    payload = status.json()
    assert payload["work_order_id"] == wo_id
    assert payload["title"]
    assert payload["status"]
    # Redaction: no notes, rates, org, tech private fields
    blob = status.text.lower()
    assert "estimate_amount" not in blob
    assert "labor_rate" not in blob
    assert "organization_id" not in blob
    assert "skill_required" not in blob
    assert "note" not in payload  # top-level notes key absent
    assert "notes" not in payload


def test_technician_cannot_create_portal_link(client, tech_token, dispatcher_token):
    wo_id = _first_wo_id(client, dispatcher_token)
    res = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(tech_token),
        json={},
    )
    assert res.status_code == 403


def test_seeded_portal_link_works(client):
    res = client.get(
        "/api/v1/public/job-status",
        params={"token": DEMO_PORTAL_RAW_TOKEN},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["customer_name"]
    assert "parts" in body


def test_expired_portal_link_404(client, dispatcher_token, db_session_factory):
    wo_id = _first_wo_id(client, dispatcher_token)
    created = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={"expire_hours": 1},
    ).json()
    raw = created["raw_token"]
    link_id = created["id"]

    db = db_session_factory()
    try:
        link = db.get(CustomerPortalLink, __import__("uuid").UUID(link_id))
        assert link is not None
        link.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()

    res = client.get("/api/v1/public/job-status", params={"token": raw})
    assert res.status_code == 404


def test_revoked_portal_link_404(client, dispatcher_token):
    wo_id = _first_wo_id(client, dispatcher_token)
    created = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={},
    ).json()
    revoke = client.post(
        f"/api/v1/portal-links/{created['id']}/revoke",
        headers=_auth(dispatcher_token),
    )
    assert revoke.status_code == 200, revoke.text
    assert revoke.json()["revoked_at"] is not None

    res = client.get(
        "/api/v1/public/job-status",
        params={"token": created["raw_token"]},
    )
    assert res.status_code == 404


def test_wrong_token_404(client):
    res = client.get(
        "/api/v1/public/job-status",
        params={"token": "this-is-not-a-valid-portal-token-xx"},
    )
    assert res.status_code == 404


def test_portal_scoped_to_one_work_order(client, dispatcher_token, db_session_factory):
    """Token for job A cannot be used to reveal job B fields beyond its own WO."""
    db = db_session_factory()
    try:
        seeded = db.scalars(
            select(WorkOrder)
            .where(
                WorkOrder.estimate_amount.is_not(None),
                WorkOrder.labor_rate.is_not(None),
                WorkOrder.archived_at.is_(None),
            )
            .limit(2)
        ).all()
        assert len(seeded) >= 2
        a_id, b_id = str(seeded[0].id), str(seeded[1].id)
        estimate = str(seeded[0].estimate_amount)
        labor_rate = str(seeded[0].labor_rate)
    finally:
        db.close()

    created = client.post(
        f"/api/v1/work-orders/{a_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={},
    ).json()
    payload = client.get(
        "/api/v1/public/job-status",
        params={"token": created["raw_token"]},
    ).json()
    assert payload["work_order_id"] == a_id
    assert payload["work_order_id"] != b_id
    assert b_id not in str(payload)

    # Rates/estimates must not leak
    blob = str(payload).lower()
    assert "estimate" not in blob
    assert "labor_rate" not in blob
    assert estimate not in str(payload)
    assert labor_rate not in str(payload)


def test_other_org_cannot_list_or_revoke(client, dispatcher_token, other_token):
    wo_id = _first_wo_id(client, dispatcher_token)
    created = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={},
    ).json()

    listed = client.get(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(other_token),
    )
    assert listed.status_code == 404

    revoked = client.post(
        f"/api/v1/portal-links/{created['id']}/revoke",
        headers=_auth(other_token),
    )
    assert revoked.status_code == 404

    # Public resolve still works for valid token (not tenant-gated by bearer)
    ok = client.get(
        "/api/v1/public/job-status",
        params={"token": created["raw_token"]},
    )
    assert ok.status_code == 200


def test_portal_create_writes_audit(client, dispatcher_token, db_session_factory):
    wo_id = _first_wo_id(client, dispatcher_token)
    created = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={},
    ).json()
    db = db_session_factory()
    try:
        row = db.scalar(
            select(AuditEvent)
            .where(
                AuditEvent.action == "portal_link.create",
                AuditEvent.entity_id == __import__("uuid").UUID(created["id"]),
            )
            .limit(1)
        )
        assert row is not None
    finally:
        db.close()


def test_token_hash_not_raw(client, dispatcher_token, db_session_factory):
    wo_id = _first_wo_id(client, dispatcher_token)
    created = client.post(
        f"/api/v1/work-orders/{wo_id}/portal-links",
        headers=_auth(dispatcher_token),
        json={},
    ).json()
    db = db_session_factory()
    try:
        link = db.get(CustomerPortalLink, __import__("uuid").UUID(created["id"]))
        assert link is not None
        assert link.token_hash == hash_portal_token(created["raw_token"])
        assert created["raw_token"] not in link.token_hash
    finally:
        db.close()

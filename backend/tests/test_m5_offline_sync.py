"""Milestone 5 — note idempotency + optimistic concurrency (409) tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi.testclient import TestClient


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_job(client: TestClient, token: str) -> dict:
    customers = client.get("/api/v1/customers", headers=_auth(token))
    assert customers.status_code == 200, customers.text
    customer_id = customers.json()["items"][0]["id"]
    start = datetime.now(tz=UTC) + timedelta(days=90)
    wo = client.post(
        "/api/v1/work-orders",
        headers=_auth(token),
        json={
            "customer_id": customer_id,
            "title": "M5 offline sync job",
            "status": "draft",
            "scheduled_start": start.isoformat(),
            "scheduled_end": (start + timedelta(hours=2)).isoformat(),
        },
    )
    assert wo.status_code == 201, wo.text
    return wo.json()


def test_note_idempotent_replay(client: TestClient, dispatcher_token: str):
    wo = _create_job(client, dispatcher_token)
    op_id = str(uuid4())
    payload = {
        "note": "Offline note for M5",
        "client_operation_id": op_id,
        "client_occurred_at": datetime.now(tz=UTC).isoformat(),
    }
    first = client.post(
        f"/api/v1/work-orders/{wo['id']}/notes",
        headers=_auth(dispatcher_token),
        json=payload,
    )
    assert first.status_code == 201, first.text
    first_body = first.json()
    assert first_body["activity_type"] == "note"
    assert first_body["client_operation_id"] == op_id

    second = client.post(
        f"/api/v1/work-orders/{wo['id']}/notes",
        headers=_auth(dispatcher_token),
        json=payload,
    )
    assert second.status_code == 200, second.text
    assert second.json()["id"] == first_body["id"]

    activities = client.get(
        f"/api/v1/work-orders/{wo['id']}/activities",
        headers=_auth(dispatcher_token),
    )
    notes = [a for a in activities.json() if a.get("client_operation_id") == op_id]
    assert len(notes) == 1


def test_status_patch_requires_base_and_conflicts(
    client: TestClient, dispatcher_token: str
):
    wo = _create_job(client, dispatcher_token)
    wo_id = wo["id"]
    base = wo["updated_at"]

    missing = client.patch(
        f"/api/v1/work-orders/{wo_id}",
        headers=_auth(dispatcher_token),
        json={"status": "in_progress"},
    )
    assert missing.status_code == 400
    assert missing.json()["detail"]["error"]["code"] == "base_updated_at_required"

    ok = client.patch(
        f"/api/v1/work-orders/{wo_id}",
        headers=_auth(dispatcher_token),
        json={"status": "en_route", "base_updated_at": base},
    )
    assert ok.status_code == 200, ok.text
    assert ok.json()["status"] == "en_route"
    server_updated = ok.json()["updated_at"]

    stale = client.patch(
        f"/api/v1/work-orders/{wo_id}",
        headers=_auth(dispatcher_token),
        json={"status": "in_progress", "base_updated_at": base},
    )
    assert stale.status_code == 409, stale.text
    err = stale.json()["detail"]["error"]
    assert err["code"] == "conflict"
    assert err["details"]["server"]["status"] == "en_route"
    assert err["details"]["server"]["updated_at"] == server_updated

    retry = client.patch(
        f"/api/v1/work-orders/{wo_id}",
        headers=_auth(dispatcher_token),
        json={"status": "in_progress", "base_updated_at": server_updated},
    )
    assert retry.status_code == 200, retry.text
    assert retry.json()["status"] == "in_progress"


def test_checklist_item_conflict(client: TestClient, dispatcher_token: str):
    wo = _create_job(client, dispatcher_token)
    checklist = client.post(
        "/api/v1/checklists",
        headers=_auth(dispatcher_token),
        json={
            "work_order_id": wo["id"],
            "name": "M5 Arrival",
            "items": ["Park safely"],
        },
    )
    assert checklist.status_code == 201, checklist.text
    item = checklist.json()["items"][0]
    item_id = item["id"]
    base = item["updated_at"]

    first = client.patch(
        f"/api/v1/checklists/items/{item_id}",
        headers=_auth(dispatcher_token),
        json={"is_completed": True, "base_updated_at": base},
    )
    assert first.status_code == 200, first.text
    assert first.json()["is_completed"] is True
    new_base = first.json()["updated_at"]

    conflict = client.patch(
        f"/api/v1/checklists/items/{item_id}",
        headers=_auth(dispatcher_token),
        json={"is_completed": False, "base_updated_at": base},
    )
    assert conflict.status_code == 409, conflict.text
    err = conflict.json()["detail"]["error"]
    assert err["code"] == "conflict"
    assert err["details"]["server"]["is_completed"] is True

    resolve = client.patch(
        f"/api/v1/checklists/items/{item_id}",
        headers=_auth(dispatcher_token),
        json={"is_completed": False, "base_updated_at": new_base},
    )
    assert resolve.status_code == 200, resolve.text
    assert resolve.json()["is_completed"] is False


def test_health_milestone_5(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["milestone"] == "5"

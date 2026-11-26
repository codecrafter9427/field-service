"""CRUD + tenant isolation for Milestone 2 endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

UTC = timezone.utc


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_customer_crud_org_scoped(client, dispatcher_token, other_token):
    create = client.post(
        "/api/v1/customers",
        headers=_auth(dispatcher_token),
        json={"name": "M2 Demo Customer", "email": "m2@demo.example", "phone": "555-2000"},
    )
    assert create.status_code == 201, create.text
    customer = create.json()
    customer_id = customer["id"]

    # Other tenant cannot read
    other_get = client.get(
        f"/api/v1/customers/{customer_id}",
        headers=_auth(other_token),
    )
    assert other_get.status_code == 404

    # Other tenant list must not include it
    other_list = client.get("/api/v1/customers", headers=_auth(other_token))
    assert other_list.status_code == 200
    assert all(item["id"] != customer_id for item in other_list.json()["items"])

    loc = client.post(
        "/api/v1/service-locations",
        headers=_auth(dispatcher_token),
        json={
            "customer_id": customer_id,
            "name": "Main Yard",
            "address_line1": "1 Dispatch Way",
            "city": "Springfield",
            "region": "IL",
            "postal_code": "62701",
            "country": "US",
        },
    )
    assert loc.status_code == 201, loc.text
    location_id = loc.json()["id"]

    other_loc = client.get(
        f"/api/v1/service-locations/{location_id}",
        headers=_auth(other_token),
    )
    assert other_loc.status_code == 404


def test_work_order_notes_checklist_time(client, dispatcher_token):
    customers = client.get("/api/v1/customers", headers=_auth(dispatcher_token))
    customer_id = customers.json()["items"][0]["id"]
    start = datetime.now(tz=UTC) + timedelta(days=60)

    wo = client.post(
        "/api/v1/work-orders",
        headers=_auth(dispatcher_token),
        json={
            "customer_id": customer_id,
            "title": "Notes checklist time job",
            "status": "draft",
            "scheduled_start": start.isoformat(),
            "scheduled_end": (start + timedelta(hours=2)).isoformat(),
        },
    )
    assert wo.status_code == 201, wo.text
    wo_id = wo.json()["id"]

    note = client.post(
        f"/api/v1/work-orders/{wo_id}/notes",
        headers=_auth(dispatcher_token),
        json={"note": "Dispatcher note for M2"},
    )
    assert note.status_code == 201
    assert note.json()["activity_type"] == "note"

    checklist = client.post(
        "/api/v1/checklists",
        headers=_auth(dispatcher_token),
        json={
            "work_order_id": wo_id,
            "name": "Arrival",
            "items": ["Park safely", "Check in with contact"],
        },
    )
    assert checklist.status_code == 201
    item_id = checklist.json()["items"][0]["id"]

    patch_item = client.patch(
        f"/api/v1/checklists/items/{item_id}",
        headers=_auth(dispatcher_token),
        json={"is_completed": True},
    )
    assert patch_item.status_code == 200
    assert patch_item.json()["is_completed"] is True

    tech_id = "00000000-0000-4000-8000-000000000002"
    time_entry = client.post(
        "/api/v1/time-entries",
        headers=_auth(dispatcher_token),
        json={
            "work_order_id": wo_id,
            "technician_id": tech_id,
            "started_at": start.isoformat(),
            "ended_at": (start + timedelta(hours=1)).isoformat(),
            "notes": "Travel + diagnose",
        },
    )
    assert time_entry.status_code == 201, time_entry.text
    assert time_entry.json()["minutes"] == 60


def test_other_org_cannot_create_on_demo_customer(client, other_token, dispatcher_token):
    customers = client.get("/api/v1/customers", headers=_auth(dispatcher_token))
    demo_customer_id = customers.json()["items"][0]["id"]

    res = client.post(
        "/api/v1/work-orders",
        headers=_auth(other_token),
        json={
            "customer_id": demo_customer_id,
            "title": "Cross-tenant attempt",
        },
    )
    assert res.status_code == 400
    assert res.json()["detail"]["error"]["code"] == "invalid_customer"

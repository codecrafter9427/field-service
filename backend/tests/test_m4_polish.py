"""Milestone 4 — assets CRUD, signoff, parts, reports, printable payload."""

from __future__ import annotations


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_milestone_4(client):
    """M4 polish suite still runs; health now reports M5."""
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["milestone"] == "6"


def test_assets_crud_and_history(client, dispatcher_token, other_token):
    customers = client.get(
        "/api/v1/customers?page_size=1", headers=_auth(dispatcher_token)
    )
    assert customers.status_code == 200
    customer_id = customers.json()["items"][0]["id"]

    created = client.post(
        "/api/v1/assets",
        headers=_auth(dispatcher_token),
        json={
            "customer_id": customer_id,
            "name": "M4 Test Boiler",
            "serial_number": "M4-SN-001",
            "asset_type": "boiler",
            "maintenance_notes": "Annual inspection due",
        },
    )
    assert created.status_code == 201, created.text
    asset_id = created.json()["id"]
    assert created.json()["name"] == "M4 Test Boiler"

    listed = client.get(
        "/api/v1/assets?q=M4%20Test", headers=_auth(dispatcher_token)
    )
    assert listed.status_code == 200
    assert any(a["id"] == asset_id for a in listed.json()["items"])

    patched = client.patch(
        f"/api/v1/assets/{asset_id}",
        headers=_auth(dispatcher_token),
        json={"maintenance_notes": "Patched notes"},
    )
    assert patched.status_code == 200
    assert patched.json()["maintenance_notes"] == "Patched notes"

    # Tenant isolation
    forbidden = client.get(
        f"/api/v1/assets/{asset_id}", headers=_auth(other_token)
    )
    assert forbidden.status_code == 404

    history = client.get(
        f"/api/v1/assets/{asset_id}/service-history",
        headers=_auth(dispatcher_token),
    )
    assert history.status_code == 200
    assert isinstance(history.json(), list)

    cust_history = client.get(
        f"/api/v1/customers/{customer_id}/service-history",
        headers=_auth(dispatcher_token),
    )
    assert cust_history.status_code == 200
    assert isinstance(cust_history.json(), list)

    archived = client.delete(
        f"/api/v1/assets/{asset_id}", headers=_auth(dispatcher_token)
    )
    assert archived.status_code == 204
    gone = client.get(f"/api/v1/assets/{asset_id}", headers=_auth(dispatcher_token))
    assert gone.status_code == 404


def test_signoff_timestamped_acknowledgement(client, dispatcher_token, other_token):
    orders = client.get(
        "/api/v1/work-orders?page_size=1", headers=_auth(dispatcher_token)
    )
    assert orders.status_code == 200
    wo_id = orders.json()["items"][0]["id"]

    created = client.post(
        f"/api/v1/work-orders/{wo_id}/signoffs",
        headers=_auth(dispatcher_token),
        json={
            "signer_name": "Pat Customer",
            "acknowledgement_text": (
                "I acknowledge the work described was completed. "
                "This is not a certified e-signature."
            ),
            "signature_data_url": "data:image/png;base64,aaa",
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["signer_name"] == "Pat Customer"
    assert body["signed_at"]
    assert body["is_certified_esignature"] is False
    assert "not a certified" in body["disclaimer"].lower()
    assert body["signature_storage_key"]

    listed = client.get(
        f"/api/v1/work-orders/{wo_id}/signoffs",
        headers=_auth(dispatcher_token),
    )
    assert listed.status_code == 200
    assert any(s["id"] == body["id"] for s in listed.json())

    # Other tenant cannot sign off
    denied = client.post(
        f"/api/v1/work-orders/{wo_id}/signoffs",
        headers=_auth(other_token),
        json={"signer_name": "Other"},
    )
    assert denied.status_code == 404


def test_parts_used_and_service_reports(client, dispatcher_token):
    orders = client.get(
        "/api/v1/work-orders?page_size=1", headers=_auth(dispatcher_token)
    )
    wo_id = orders.json()["items"][0]["id"]

    part = client.post(
        "/api/v1/parts-used",
        headers=_auth(dispatcher_token),
        json={
            "work_order_id": wo_id,
            "part_name": "M4 Filter Cartridge",
            "quantity": "2",
            "unit_cost": "15.50",
        },
    )
    assert part.status_code == 201, part.text
    assert part.json()["line_total"] == "31.00"

    parts = client.get(
        f"/api/v1/parts-used?work_order_id={wo_id}",
        headers=_auth(dispatcher_token),
    )
    assert parts.status_code == 200
    assert any(p["part_name"] == "M4 Filter Cartridge" for p in parts.json())

    summary = client.get("/api/v1/reports/service", headers=_auth(dispatcher_token))
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_jobs"] >= 1
    assert "completion_rate" in data
    assert isinstance(data["labor"], list)
    assert isinstance(data["parts"], list)
    assert any(p["part_name"] == "M4 Filter Cartridge" for p in data["parts"])

    printable = client.get(
        f"/api/v1/reports/service/work-orders/{wo_id}",
        headers=_auth(dispatcher_token),
    )
    assert printable.status_code == 200
    report = printable.json()
    assert report["work_order"]["id"] == wo_id
    assert "print_hint" in report
    assert isinstance(report["notes"], list)
    assert isinstance(report["checklists"], list)
    assert isinstance(report["parts"], list)
    assert isinstance(report["signoffs"], list)

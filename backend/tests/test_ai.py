"""Tests for Demo AI, Service Memory retrieval, and AI auth gates."""

from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.ai.demo import DemoAIProvider
from app.core.database import SessionLocal
from app.models import Asset, Customer, WorkOrder
from scripts.seed import DEMO_ORG_ID


def test_demo_ai_service_report_deterministic():
    provider = DemoAIProvider()

    async def _run():
        a = await provider.generate_structured(
            task="service_report",
            input_text="Filter clogged; low airflow on rooftop unit.",
            context={"title": "HVAC filter service", "asset_name": "Rooftop HVAC Unit A"},
        )
        b = await provider.generate_structured(
            task="service_report",
            input_text="Filter clogged; low airflow on rooftop unit.",
            context={"title": "HVAC filter service", "asset_name": "Rooftop HVAC Unit A"},
        )
        return a, b

    a, b = asyncio.run(_run())
    assert a["provider"] == "demo"
    assert a["problem"]
    assert a["diagnosis"]
    assert a["work_performed"]
    assert a == b
    assert "edit" in a["follow_up"].lower()


def test_demo_ai_job_prep_suggests_checklist():
    provider = DemoAIProvider()
    result = asyncio.run(
        provider.generate_structured(
            task="job_prep",
            input_text="Quarterly HVAC filter service",
            context={
                "title": "Quarterly HVAC filter service",
                "asset_type": "HVAC",
                "history_highlights": ["Prior filter clog visit"],
                "existing_checklist": ["Arrive on site"],
            },
        )
    )
    assert result["provider"] == "demo"
    assert result["job_type"] == "hvac"
    assert result["suggested_checklist"]
    assert all(not s["confirmed"] for s in result["suggested_checklist"])


def test_demo_ai_service_memory_uses_theme_context():
    provider = DemoAIProvider()
    result = asyncio.run(
        provider.generate_structured(
            task="service_memory",
            input_text="filter",
            context={
                "hit_count": 3,
                "theme_counts": {"filter": 5, "clog": 3},
                "asset_names": ["Rooftop HVAC Unit A"],
                "titles": ["Quarterly HVAC filter service"],
            },
        )
    )
    assert result["provider"] == "demo"
    assert result["recurring_themes"]
    assert "filter" in result["recurring_themes"][0].lower()
    assert "confirm" in result["suggested_follow_up"].lower()


def test_ai_endpoints_require_auth(client: TestClient):
    for path in (
        "/api/v1/ai/service-report",
        "/api/v1/ai/job-prep",
        "/api/v1/ai/service-memory",
        "/api/v1/ai/service-report/approve",
        "/api/v1/ai/job-prep/confirm-checklist",
    ):
        res = client.post(path, json={})
        assert res.status_code == 401, path


def test_service_report_draft_and_approve(client: TestClient, tech_token: str):
    headers = {"Authorization": f"Bearer {tech_token}"}
    # Pick a seeded work order
    db = SessionLocal()
    try:
        wo = db.scalar(
            select(WorkOrder).where(WorkOrder.organization_id == DEMO_ORG_ID).limit(1)
        )
        assert wo is not None
        wo_id = str(wo.id)
        status_before = wo.status
    finally:
        db.close()

    draft = client.post(
        "/api/v1/ai/service-report",
        headers=headers,
        json={"work_order_id": wo_id, "notes": "Filter clogged; cleaned contacts."},
    )
    assert draft.status_code == 200, draft.text
    body = draft.json()
    assert body["requires_confirmation"] is True
    assert body["draft"]["problem"]
    assert "complete_job" in body["ai_cannot"]
    assert body["provider"] in ("demo", "demo-fallback", "ollama")

    # Approve without edited flag should fail
    bad = client.post(
        "/api/v1/ai/service-report/approve",
        headers=headers,
        json={
            "work_order_id": wo_id,
            "problem": body["draft"]["problem"],
            "diagnosis": body["draft"]["diagnosis"],
            "work_performed": body["draft"]["work_performed"],
            "parts": body["draft"]["parts"],
            "follow_up": body["draft"]["follow_up"],
            "edited": False,
        },
    )
    assert bad.status_code == 400

    ok = client.post(
        "/api/v1/ai/service-report/approve",
        headers=headers,
        json={
            "work_order_id": wo_id,
            "problem": "Edited: intermittent filter restriction",
            "diagnosis": body["draft"]["diagnosis"],
            "work_performed": "Replaced filter; verified airflow",
            "parts": ["Filter media pack"],
            "follow_up": "Quarterly PM",
            "edited": True,
        },
    )
    assert ok.status_code == 200, ok.text
    approved = ok.json()
    assert approved["approved"] is True
    assert approved["status_unchanged"] == status_before
    assert approved["attachment_id"]


def test_job_prep_and_confirm_checklist(client: TestClient, dispatcher_token: str):
    headers = {"Authorization": f"Bearer {dispatcher_token}"}
    db = SessionLocal()
    try:
        wo = db.scalar(
            select(WorkOrder)
            .where(
                WorkOrder.organization_id == DEMO_ORG_ID,
                WorkOrder.title.ilike("%HVAC%"),
            )
            .limit(1)
        )
        assert wo is not None
        wo_id = str(wo.id)
    finally:
        db.close()

    prep = client.post(
        "/api/v1/ai/job-prep",
        headers=headers,
        json={"work_order_id": wo_id},
    )
    assert prep.status_code == 200, prep.text
    data = prep.json()
    assert data["requires_confirmation"] is True
    assert data["summary"]
    assert data["suggested_checklist"]
    label = data["suggested_checklist"][0]["label"]

    confirm = client.post(
        "/api/v1/ai/job-prep/confirm-checklist",
        headers=headers,
        json={"work_order_id": wo_id, "items": [label]},
    )
    assert confirm.status_code == 200, confirm.text
    assert label in confirm.json()["added_labels"]


def test_service_memory_retrieval_by_query(client: TestClient, dispatcher_token: str):
    headers = {"Authorization": f"Bearer {dispatcher_token}"}
    res = client.post(
        "/api/v1/ai/service-memory",
        headers=headers,
        json={"query": "filter", "limit": 10},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["requires_confirmation"] is True
    assert body["hits"], "Expected seeded filter-related history hits"
    assert body["recurring_themes"]
    assert body["sources"]
    assert "confirm" in body["explanation"].lower() or body["requires_confirmation"]


def test_service_memory_by_asset(client: TestClient, dispatcher_token: str):
    headers = {"Authorization": f"Bearer {dispatcher_token}"}
    db = SessionLocal()
    try:
        asset = db.scalar(
            select(Asset)
            .where(Asset.organization_id == DEMO_ORG_ID, Asset.asset_type == "HVAC")
            .limit(1)
        )
        assert asset is not None
        asset_id = str(asset.id)
    finally:
        db.close()

    res = client.post(
        "/api/v1/ai/service-memory",
        headers=headers,
        json={"asset_id": asset_id, "query": "", "limit": 15},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["hits"]
    for hit in body["hits"]:
        assert hit["asset_id"] == asset_id


def test_service_memory_tenant_isolation(client: TestClient, other_token: str):
    headers = {"Authorization": f"Bearer {other_token}"}
    db = SessionLocal()
    try:
        asset = db.scalar(
            select(Asset).where(Asset.organization_id == DEMO_ORG_ID).limit(1)
        )
        assert asset is not None
        asset_id = str(asset.id)
        customer = db.scalar(
            select(Customer).where(Customer.organization_id == DEMO_ORG_ID).limit(1)
        )
        assert customer is not None
        customer_id = str(customer.id)
    finally:
        db.close()

    # Other tenant cannot read demo org asset
    res = client.post(
        "/api/v1/ai/service-memory",
        headers=headers,
        json={"asset_id": asset_id},
    )
    assert res.status_code == 404

    res2 = client.post(
        "/api/v1/ai/service-memory",
        headers=headers,
        json={"customer_id": customer_id},
    )
    assert res2.status_code == 404


def test_service_report_tenant_isolation(client: TestClient, other_token: str):
    headers = {"Authorization": f"Bearer {other_token}"}
    db = SessionLocal()
    try:
        wo = db.scalar(
            select(WorkOrder).where(WorkOrder.organization_id == DEMO_ORG_ID).limit(1)
        )
        assert wo is not None
        wo_id = str(wo.id)
    finally:
        db.close()

    res = client.post(
        "/api/v1/ai/service-report",
        headers=headers,
        json={"work_order_id": wo_id},
    )
    assert res.status_code == 404


def test_health_milestone_3(client: TestClient):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["milestone"] == "3"

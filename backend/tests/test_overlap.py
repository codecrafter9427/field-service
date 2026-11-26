"""Schedule overlap warning tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

TECH_ID = "00000000-0000-4000-8000-000000000002"
UTC = timezone.utc


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_job(client, token: str, *, title: str, start: datetime, end: datetime) -> dict:
    customers = client.get("/api/v1/customers", headers=_auth(token))
    assert customers.status_code == 200
    customer_id = customers.json()["items"][0]["id"]

    locations = client.get(
        f"/api/v1/service-locations?customer_id={customer_id}",
        headers=_auth(token),
    )
    assert locations.status_code == 200
    location_id = locations.json()["items"][0]["id"] if locations.json()["items"] else None

    res = client.post(
        "/api/v1/work-orders",
        headers=_auth(token),
        json={
            "customer_id": customer_id,
            "service_location_id": location_id,
            "title": title,
            "status": "scheduled",
            "priority": "normal",
            "scheduled_start": start.isoformat(),
            "scheduled_end": end.isoformat(),
            "technician_id": TECH_ID,
        },
    )
    assert res.status_code == 201, res.text
    return res.json()


def test_assign_warns_on_overlapping_jobs(client, dispatcher_token):
    start = datetime.now(tz=UTC) + timedelta(days=30)
    end = start + timedelta(hours=2)

    first = _create_job(
        client,
        dispatcher_token,
        title="Overlap base job",
        start=start,
        end=end,
    )
    assert first["overlap_warning"] is False

    second = _create_job(
        client,
        dispatcher_token,
        title="Overlap conflicting job",
        start=start + timedelta(hours=1),
        end=end + timedelta(hours=1),
    )
    assert second["overlap_warning"] is True
    assert first["id"] in second["overlapping_work_order_ids"]

    schedule = client.get(
        "/api/v1/schedule",
        headers=_auth(dispatcher_token),
        params={"technician_id": TECH_ID},
    )
    assert schedule.status_code == 200
    flagged = [item for item in schedule.json() if item["work_order_id"] == second["id"]]
    assert flagged
    assert flagged[0]["overlap_warning"] is True


def test_non_overlapping_jobs_no_warning(client, dispatcher_token):
    start = datetime.now(tz=UTC) + timedelta(days=40)
    first = _create_job(
        client,
        dispatcher_token,
        title="Non-overlap A",
        start=start,
        end=start + timedelta(hours=2),
    )
    second = _create_job(
        client,
        dispatcher_token,
        title="Non-overlap B",
        start=start + timedelta(hours=3),
        end=start + timedelta(hours=5),
    )
    assert first["overlap_warning"] is False
    assert second["overlap_warning"] is False


def test_created_job_appears_in_agenda(client, dispatcher_token, tech_token):
    start = datetime.now(tz=UTC) + timedelta(days=50)
    job = _create_job(
        client,
        dispatcher_token,
        title="Agenda visibility job",
        start=start,
        end=start + timedelta(hours=2),
    )

    agenda = client.get("/api/v1/assignments/agenda", headers=_auth(tech_token))
    assert agenda.status_code == 200
    ids = {item["work_order_id"] for item in agenda.json()}
    assert job["id"] in ids

    assignments = client.get(
        "/api/v1/assignments",
        headers=_auth(dispatcher_token),
        params={"technician_id": TECH_ID},
    )
    assert assignments.status_code == 200
    assert any(item["work_order_id"] == job["id"] for item in assignments.json()["items"])

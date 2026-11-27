"""M6 Insights connector — read-only summary + role gates."""


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_connector_health(client, dispatcher_token):
    res = client.get(
        "/api/v1/connectors/insights/v1/health",
        headers=_auth(dispatcher_token),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "ok"
    assert body["product"] == "field-service"
    assert body["connector"] == "insights"
    assert body["version"] == "v1"
    assert body["milestone"] == "6"


def test_connector_summary_shape(client, dispatcher_token):
    res = client.get(
        "/api/v1/connectors/insights/v1/summary",
        headers=_auth(dispatcher_token),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["source_product"] == "field-service"
    assert body["connector_version"] == "v1"
    assert "organization_id" in body
    assert "jobs_by_status" in body
    assert "completion_rate" in body
    assert "labor" in body
    assert "parts" in body
    assert isinstance(body["total_jobs"], int)


def test_connector_subpaths(client, dispatcher_token):
    for path in ("/jobs-by-status", "/completion", "/labor", "/parts"):
        res = client.get(
            f"/api/v1/connectors/insights/v1{path}",
            headers=_auth(dispatcher_token),
        )
        assert res.status_code == 200, f"{path}: {res.text}"


def test_technician_blocked_from_connector(client, tech_token):
    res = client.get(
        "/api/v1/connectors/insights/v1/summary",
        headers=_auth(tech_token),
    )
    assert res.status_code == 403


def test_connector_org_isolation(client, dispatcher_token, other_token):
    demo = client.get(
        "/api/v1/connectors/insights/v1/summary",
        headers=_auth(dispatcher_token),
    ).json()
    other = client.get(
        "/api/v1/connectors/insights/v1/summary",
        headers=_auth(other_token),
    ).json()
    assert demo["organization_id"] != other["organization_id"]
    # Other tenant seed has far fewer jobs
    assert other["total_jobs"] < demo["total_jobs"]


def test_connector_key_required_when_configured(client, dispatcher_token, monkeypatch):
    from app.core import config as config_mod

    monkeypatch.setattr(config_mod.settings, "insights_connector_key", "test-connector-key")
    denied = client.get(
        "/api/v1/connectors/insights/v1/health",
        headers=_auth(dispatcher_token),
    )
    assert denied.status_code == 401
    ok = client.get(
        "/api/v1/connectors/insights/v1/health",
        headers={**_auth(dispatcher_token), "X-Connector-Key": "test-connector-key"},
    )
    assert ok.status_code == 200

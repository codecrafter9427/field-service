"""Organization scoping smoke tests."""

DEMO_ORG = "00000000-0000-4000-8000-000000000010"
OTHER_ORG = "00000000-0000-4000-8000-000000000099"


def test_customers_scoped_to_demo_org(client, dispatcher_token):
    res = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {dispatcher_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["meta"]["total"] == 12
    assert len(body["items"]) == 12
    assert all(item["organization_id"] == DEMO_ORG for item in body["items"])
    names = {item["name"] for item in body["items"]}
    assert "Secret Other Tenant Site" not in names


def test_other_org_cannot_see_demo_customers(client, other_token):
    res = client.get(
        "/api/v1/customers",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["meta"]["total"] == 1
    assert body["items"][0]["organization_id"] == OTHER_ORG
    assert body["items"][0]["name"] == "Secret Other Tenant Site"


def test_work_orders_scoped_to_org(client, tech_token, other_token):
    demo = client.get(
        "/api/v1/work-orders",
        headers={"Authorization": f"Bearer {tech_token}"},
    )
    assert demo.status_code == 200
    assert demo.json()["meta"]["total"] == 20
    assert all(item["organization_id"] == DEMO_ORG for item in demo.json()["items"])

    other = client.get(
        "/api/v1/work-orders",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other.status_code == 200
    assert other.json()["meta"]["total"] == 0


def test_customers_require_auth(client):
    res = client.get("/api/v1/customers")
    assert res.status_code == 401

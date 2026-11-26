"""Demo auth smoke tests."""


def test_demo_login_dispatcher(client):
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "dispatcher@demo.local", "password": "demo"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"].startswith("demo:")
    assert body["user"]["role"] == "dispatcher"
    assert body["user"]["email"] == "dispatcher@demo.local"
    assert body["user"]["organization_id"]


def test_demo_login_technician(client):
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "tech@demo.local", "password": "demo"},
    )
    assert res.status_code == 200
    assert res.json()["user"]["role"] == "technician"


def test_demo_login_invalid_password(client):
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "dispatcher@demo.local", "password": "wrong"},
    )
    assert res.status_code == 401


def test_me_requires_auth(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_with_token(client, dispatcher_token):
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {dispatcher_token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "dispatcher@demo.local"

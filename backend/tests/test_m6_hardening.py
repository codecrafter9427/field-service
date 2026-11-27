"""M6 hardening — signed tokens, expiry, rate limit, password policy."""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID

from app.core.config import Settings
from app.core.password_policy import password_meets_policy
from app.core.rate_limit import reset_rate_limits
from app.core.security import (
    create_access_token,
    hash_password,
    parse_access_token,
    verify_password,
)


def test_demo_login_returns_signed_token(client):
    res = client.post(
        "/api/v1/auth/demo-login",
        json={"email": "dispatcher@demo.local", "password": "demo"},
    )
    assert res.status_code == 200
    token = res.json()["access_token"]
    assert not token.startswith("demo:")
    assert token.startswith("fs1.")
    payload = parse_access_token(token)
    assert payload is not None
    assert payload["email"] == "dispatcher@demo.local"
    assert payload["role"] == "dispatcher"


def test_me_with_signed_token(client, dispatcher_token):
    assert dispatcher_token.startswith("fs1.")
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {dispatcher_token}"},
    )
    assert res.status_code == 200
    assert res.json()["email"] == "dispatcher@demo.local"


def test_expired_staff_token_401(client):
    token = create_access_token(
        user_id=UUID("00000000-0000-4000-8000-000000000001"),
        organization_id=UUID("00000000-0000-4000-8000-000000000010"),
        role="dispatcher",
        email="dispatcher@demo.local",
        expire_minutes=-1,
    )
    assert parse_access_token(token) is None
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 401


def test_forged_staff_token_401(client, dispatcher_token):
    forged = dispatcher_token[:-4] + (
        "abcd" if not dispatcher_token.endswith("abcd") else "efgh"
    )
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged}"},
    )
    assert res.status_code == 401


def test_password_hash_encodes_iterations():
    hashed = hash_password("demo")
    parts = hashed.split("$")
    assert parts[0] == "pbkdf2_sha256"
    assert parts[1].isdigit()
    assert int(parts[1]) >= 100_000
    assert verify_password("demo", hashed)
    # Legacy 3-part format (no iterations) still verifies at default iters
    salt, digest = parts[2], parts[3]
    legacy = f"pbkdf2_sha256${salt}${digest}"
    assert verify_password("demo", legacy)


def test_password_policy_demo_vs_prod():
    assert password_meets_policy("demo") is True
    with patch("app.core.password_policy.settings") as mock_settings:
        mock_settings.demo_auth_enabled = False
        assert password_meets_policy("short") is False
        assert password_meets_policy("longenough") is True


def test_login_rate_limit_429(client, monkeypatch):
    from app.core import config as config_mod

    reset_rate_limits()
    monkeypatch.setattr(config_mod.settings, "rate_limit_login_per_minute", 3)
    limited = False
    for _ in range(6):
        res = client.post(
            "/api/v1/auth/demo-login",
            json={"email": "dispatcher@demo.local", "password": "wrong"},
        )
        if res.status_code == 429:
            limited = True
            break
    assert limited
    reset_rate_limits()


def test_settings_placeholder_detection():
    s = Settings(secret_key="replace_with_local_demo_secret")
    assert s.is_placeholder_secret is True
    s2 = Settings(secret_key="a-strong-local-secret-value")
    assert s2.is_placeholder_secret is False

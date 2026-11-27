"""Password hashing and signed access tokens — portfolio demo grade, not production."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any
from uuid import UUID

from app.core.config import settings

_PBKDF2_ITERATIONS = 120_000
_TOKEN_PREFIX = "fs1."


def hash_password(password: str, salt: str | None = None, *, iterations: int | None = None) -> str:
    """PBKDF2-SHA256 with iterations encoded in the hash string."""
    salt = salt or secrets.token_hex(16)
    iters = iterations or _PBKDF2_ITERATIONS
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iters
    )
    return f"pbkdf2_sha256${iters}${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    """Accept new (`pbkdf2_sha256$iters$salt$hex`) and legacy (`pbkdf2_sha256$salt$hex`) formats."""
    try:
        parts = password_hash.split("$")
    except AttributeError:
        return False
    if len(parts) == 4 and parts[0] == "pbkdf2_sha256":
        scheme, iters_s, salt, expected = parts
        try:
            iterations = int(iters_s)
        except ValueError:
            return False
    elif len(parts) == 3 and parts[0] == "pbkdf2_sha256":
        scheme, salt, expected = parts
        iterations = _PBKDF2_ITERATIONS
    else:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
    )
    return hmac.compare_digest(digest.hex(), expected)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_access_token(
    *,
    user_id: UUID,
    organization_id: UUID,
    role: str,
    email: str,
    expire_minutes: int | None = None,
) -> str:
    """HMAC-signed opaque staff token. Mobile/web treat the string as opaque."""
    now = int(time.time())
    ttl = expire_minutes if expire_minutes is not None else settings.access_token_expire_minutes
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "org": str(organization_id),
        "role": role,
        "email": email.strip().lower(),
        "iat": now,
        "exp": now + int(ttl) * 60,
    }
    body = _b64url_encode(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8"))
    sig = _b64url_encode(
        hmac.new(
            settings.secret_key.encode("utf-8"),
            body.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    return f"{_TOKEN_PREFIX}{body}.{sig}"


def parse_access_token(token: str) -> dict[str, Any] | None:
    """Validate HMAC + expiry. Returns payload or None."""
    if not token.startswith(_TOKEN_PREFIX):
        # Legacy demo tokens no longer accepted after M6 signed-token cutover.
        return None
    rest = token.removeprefix(_TOKEN_PREFIX)
    try:
        body, sig = rest.rsplit(".", 1)
    except ValueError:
        return None
    expected = _b64url_encode(
        hmac.new(
            settings.secret_key.encode("utf-8"),
            body.encode("ascii"),
            hashlib.sha256,
        ).digest()
    )
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        payload = json.loads(_b64url_decode(body).decode("utf-8"))
    except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None
    return payload


# Back-compat aliases used by older imports / seed surface
def make_demo_token(email: str) -> str:  # pragma: no cover - legacy helper
    raise RuntimeError("Use create_access_token; demo: tokens are retired in M6")


def parse_demo_token(token: str) -> str | None:  # pragma: no cover
    payload = parse_access_token(token)
    if not payload:
        return None
    email = payload.get("email")
    return str(email).lower() if email else None


def generate_portal_token() -> str:
    return secrets.token_urlsafe(32)


def hash_portal_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

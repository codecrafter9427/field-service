"""Demo password hashing and token helpers — not production-secure."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def hash_password(password: str, salt: str | None = None) -> str:
    """PBKDF2-SHA256 hash suitable for local demo credentials only."""
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    )
    return f"pbkdf2_sha256${salt}${digest.hex()}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        scheme, salt, expected = password_hash.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000
    )
    return hmac.compare_digest(digest.hex(), expected)


def make_demo_token(email: str) -> str:
    return f"demo:{email.strip().lower()}"


def parse_demo_token(token: str) -> str | None:
    if not token.startswith("demo:"):
        return None
    email = token.removeprefix("demo:").strip().lower()
    return email or None

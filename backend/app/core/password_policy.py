"""Password policy helpers (demo-friendly)."""

from __future__ import annotations

from app.core.config import settings


def password_meets_policy(password: str) -> bool:
    """Demo auth allows short seed passwords; non-demo requires ≥8 chars."""
    if settings.demo_auth_enabled:
        return len(password) >= 1
    return len(password) >= 8

"""Demo login against seeded org-scoped users."""

from __future__ import annotations

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.api.errors import api_error
from app.core.config import settings
from app.core.password_policy import password_meets_policy
from app.core.rate_limit import check_rate_limit, client_ip
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import AuthUser, DemoLoginRequest, DemoLoginResponse
from starlette import status

router = APIRouter()


@router.post("/demo-login", response_model=DemoLoginResponse)
def demo_login(body: DemoLoginRequest, request: Request, db: DbSession) -> DemoLoginResponse:
    check_rate_limit(
        f"login:{client_ip(request)}",
        limit=settings.rate_limit_login_per_minute,
    )

    if not settings.demo_auth_enabled:
        raise api_error(
            status.HTTP_403_FORBIDDEN,
            "demo_auth_disabled",
            "Demo authentication is disabled",
        )

    if not password_meets_policy(body.password):
        raise api_error(
            status.HTTP_400_BAD_REQUEST,
            "password_too_short",
            "Password does not meet policy",
        )

    email = str(body.email).strip().lower()
    user = db.scalar(
        select(User).where(
            User.email == email,
            User.is_active.is_(True),
            User.archived_at.is_(None),
        )
    )
    if user is None or not verify_password(body.password, user.password_hash):
        raise api_error(
            status.HTTP_401_UNAUTHORIZED,
            "invalid_credentials",
            "Invalid demo credentials",
        )

    token = create_access_token(
        user_id=user.id,
        organization_id=user.organization_id,
        role=user.role,
        email=user.email,
    )
    return DemoLoginResponse(
        access_token=token,
        user=AuthUser(
            id=user.id,
            email=user.email,
            role=user.role,
            organization_id=user.organization_id,
            display_name=user.display_name,
        ),
    )


@router.get("/me", response_model=AuthUser)
def me(user: CurrentUser) -> AuthUser:
    return AuthUser(
        id=user.id,
        email=user.email,
        role=user.role,
        organization_id=user.organization_id,
        display_name=user.display_name,
    )


__all__ = ["router", "hash_password"]

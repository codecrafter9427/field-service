"""Demo login against seeded org-scoped users."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import hash_password, make_demo_token, verify_password
from app.models import User
from app.schemas.auth import AuthUser, DemoLoginRequest, DemoLoginResponse

router = APIRouter()


@router.post("/demo-login", response_model=DemoLoginResponse)
def demo_login(body: DemoLoginRequest, db: DbSession) -> DemoLoginResponse:
    if not settings.demo_auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "demo_auth_disabled",
                    "message": "Demo authentication is disabled",
                    "details": None,
                }
            },
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "invalid_credentials",
                    "message": "Invalid demo credentials",
                    "details": None,
                }
            },
        )

    return DemoLoginResponse(
        access_token=make_demo_token(user.email),
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


# Keep hash_password import used by seed/tests via public surface
__all__ = ["router", "hash_password"]

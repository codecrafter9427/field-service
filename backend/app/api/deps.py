"""FastAPI dependencies — DB session, current user, org scoping, roles."""

from __future__ import annotations

from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import parse_access_token
from app.models import User
from app.models.enums import UserRole


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Resolve signed bearer token to an active org-scoped user."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Missing bearer token",
                    "details": None,
                }
            },
        )
    token = authorization.split(" ", 1)[1].strip()
    payload = parse_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Invalid or expired access token",
                    "details": None,
                }
            },
        )
    email = str(payload.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Invalid access token payload",
                    "details": None,
                }
            },
        )
    user = db.scalar(
        select(User).where(
            User.email == email,
            User.is_active.is_(True),
            User.archived_at.is_(None),
        )
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Unknown or inactive user",
                    "details": None,
                }
            },
        )
    return user


def require_org_match(user: User, organization_id: UUID) -> None:
    if user.organization_id != organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "forbidden_tenant",
                    "message": "Resource is outside your organization",
                    "details": None,
                }
            },
        )


def require_roles(*roles: UserRole | str) -> Callable[[User], User]:
    allowed = {
        (r.value if isinstance(r, UserRole) else str(r)).lower() for r in roles
    }

    def _dep(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role.lower() not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "forbidden_role",
                        "message": "Insufficient role for this action",
                        "details": {"required_roles": sorted(allowed)},
                    }
                },
            )
        return user

    return _dep


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]
DispatcherUser = Annotated[
    User, Depends(require_roles(UserRole.ADMIN, UserRole.DISPATCHER))
]

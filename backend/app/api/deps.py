"""FastAPI dependencies — DB session, current user, org scoping."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import parse_demo_token
from app.models import User


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    """Resolve demo bearer token `demo:<email>` to an active org-scoped user."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Missing demo bearer token",
                    "details": None,
                }
            },
        )
    token = authorization.split(" ", 1)[1].strip()
    email = parse_demo_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "unauthorized",
                    "message": "Invalid demo token",
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
                    "message": "Unknown or inactive demo user",
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


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[Session, Depends(get_db)]

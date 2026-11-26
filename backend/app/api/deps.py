"""FastAPI dependencies (stubs)."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.security import DEMO_USERS, DemoUser


def get_current_demo_user(
    authorization: Annotated[str | None, Header()] = None,
) -> DemoUser:
    """Very light demo bearer: token format `demo:<email>`."""
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
    if token.startswith("demo:"):
        email = token.removeprefix("demo:").lower()
        entry = DEMO_USERS.get(email)
        if entry:
            return entry[1]
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


CurrentDemoUser = Annotated[DemoUser, Depends(get_current_demo_user)]

"""Demo auth placeholder — not production-secure."""

from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass(frozen=True)
class DemoUser:
    id: str
    email: str
    role: str
    organization_id: str
    display_name: str


# Fictional demo users only
DEMO_USERS: dict[str, tuple[str, DemoUser]] = {
    "dispatcher@demo.local": (
        "demo",
        DemoUser(
            id="00000000-0000-4000-8000-000000000001",
            email="dispatcher@demo.local",
            role="dispatcher",
            organization_id="00000000-0000-4000-8000-000000000010",
            display_name="Dana Dispatcher",
        ),
    ),
    "tech@demo.local": (
        "demo",
        DemoUser(
            id="00000000-0000-4000-8000-000000000002",
            email="tech@demo.local",
            role="technician",
            organization_id="00000000-0000-4000-8000-000000000010",
            display_name="Terry Technician",
        ),
    ),
}


def authenticate_demo(email: str, password: str) -> DemoUser:
    entry = DEMO_USERS.get(email.lower().strip())
    if entry is None or entry[0] != password:
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
    return entry[1]

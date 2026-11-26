"""Demo login placeholder."""

from fastapi import APIRouter

from app.core.security import authenticate_demo
from app.schemas.common import DemoLoginRequest, DemoLoginResponse

router = APIRouter()


@router.post("/demo-login", response_model=DemoLoginResponse)
def demo_login(body: DemoLoginRequest) -> DemoLoginResponse:
    user = authenticate_demo(body.email, body.password)
    return DemoLoginResponse(
        access_token=f"demo:{user.email}",
        user={
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "organization_id": user.organization_id,
            "display_name": user.display_name,
        },
    )

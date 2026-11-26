from fastapi import APIRouter

from app.api.v1._coming_soon import coming_soon
from app.schemas.common import ComingSoonResponse

router = APIRouter()


@router.get("", response_model=ComingSoonResponse)
def list_assets() -> ComingSoonResponse:
    return coming_soon("assets")

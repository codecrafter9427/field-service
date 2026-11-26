from fastapi import APIRouter

from app.api.v1._coming_soon import coming_soon
from app.schemas.common import ComingSoonResponse

router = APIRouter()


@router.get("", response_model=ComingSoonResponse)
def get_schedule() -> ComingSoonResponse:
    return coming_soon("schedule")

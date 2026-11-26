from fastapi import APIRouter

from app.api.v1._coming_soon import coming_soon
from app.schemas.common import ComingSoonResponse

router = APIRouter()


@router.get("/service", response_model=ComingSoonResponse)
def service_reports() -> ComingSoonResponse:
    return coming_soon("reports/service")

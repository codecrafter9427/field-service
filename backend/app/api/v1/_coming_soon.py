"""Helper for Coming Soon stub routes."""

from app.schemas.common import ComingSoonResponse


def coming_soon(feature: str) -> ComingSoonResponse:
    return ComingSoonResponse(feature=feature)

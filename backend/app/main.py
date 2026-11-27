"""FastAPI application entrypoint — Field Service Milestone 6."""

from __future__ import annotations

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

logger = logging.getLogger("field_service")


def _guard_production_secrets() -> None:
    """Hard-fail when production-like mode uses placeholder secrets."""
    env = (settings.environment or "demo").strip().lower()
    prod_like = env in {"production", "prod"} or not settings.demo_auth_enabled
    if prod_like and settings.is_placeholder_secret:
        logger.error(
            "SECRET_KEY is a placeholder while DEMO_AUTH_ENABLED=false or ENVIRONMENT=production"
        )
        sys.exit(1)
    if settings.is_placeholder_secret:
        logger.warning(
            "SECRET_KEY is a local demo placeholder — fine for demo, replace before any shared deploy"
        )


_guard_production_secrets()

app = FastAPI(
    title="Field Service API",
    version="0.6.0",
    description=(
        "Portfolio MVP Milestone 6 — customer job-status portal, signed staff tokens, "
        "rate limits, and Insights connector. Preserves M5 offline note/status/checklist sync. "
        "No paid APIs."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "field-service",
        "milestone": "6",
        "ai_provider": settings.ai_provider,
    }


app.include_router(api_router, prefix="/api/v1")

"""FastAPI application entrypoint — Field Service Milestone 4."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Field Service API",
    version="0.4.0",
    description=(
        "Portfolio MVP Milestone 4 — printable service reports, acknowledgement "
        "signoff, assets CRUD, labor/parts reports, polished dispatcher UX. "
        "No paid APIs. Offline sync and certified e-sign remain out of scope."
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
        "milestone": "4",
        "ai_provider": settings.ai_provider,
    }


app.include_router(api_router, prefix="/api/v1")

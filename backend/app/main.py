"""FastAPI application entrypoint — Field Service Milestone 1."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Field Service API",
    version="0.1.0",
    description=(
        "Portfolio MVP Milestone 1 — auth, org-scoped seed data, health. "
        "Full scheduling/offline/signature/AI reports are later milestones."
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
    return {"status": "ok", "service": "field-service", "milestone": "1"}


app.include_router(api_router, prefix="/api/v1")

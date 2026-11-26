"""FastAPI application entrypoint — Field Service Milestone 2."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Field Service API",
    version="0.2.0",
    description=(
        "Portfolio MVP Milestone 2 — customers/locations/work-order CRUD, "
        "assignments, schedule overlap warnings, notes/checklist/time APIs. "
        "Offline sync, signature capture, and AI reports are later milestones."
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
    return {"status": "ok", "service": "field-service", "milestone": "2"}


app.include_router(api_router, prefix="/api/v1")

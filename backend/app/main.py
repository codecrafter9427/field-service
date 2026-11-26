"""FastAPI application entrypoint — Field Service Milestone 3."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Field Service API",
    version="0.3.0",
    description=(
        "Portfolio MVP Milestone 3 — AI service reports, job prep, Service Memory. "
        "DemoAIProvider is default; Ollama is optional. "
        "Offline sync and signature capture remain later milestones."
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
        "milestone": "3",
        "ai_provider": settings.ai_provider,
    }


app.include_router(api_router, prefix="/api/v1")

"""FastAPI application entrypoint — Field Service skeleton."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings

app = FastAPI(
    title="Field Service API",
    version="0.1.0",
    description="Portfolio MVP skeleton — scheduling/dispatch stubs only.",
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
    return {"status": "ok", "service": "field-service"}


app.include_router(api_router, prefix="/api/v1")

"""Ollama adapter stub — local open models only; not wired for full generation yet."""

from typing import Any

import httpx

from app.ai.provider import AIProvider
from app.core.config import settings


class OllamaAIProvider(AIProvider):
    """
    Thin stub that probes Ollama availability.
    Full structured generation is backlog; falls back to a clear stub payload.
    """

    async def generate_structured(
        self,
        *,
        task: str,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        available = await self._ping()
        return {
            "task": task,
            "provider": "ollama",
            "ollama_reachable": available,
            "model": settings.ollama_model,
            "message": (
                "Ollama adapter stub only — structured report generation not implemented yet. "
                "Set AI_PROVIDER=demo for deterministic demo output."
            ),
            "input_preview": input_text[:200],
            "context_keys": list((context or {}).keys()),
        }

    async def _ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{settings.ollama_base_url.rstrip('/')}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

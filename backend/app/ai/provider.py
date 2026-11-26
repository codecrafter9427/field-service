"""AIProvider interface and factory — backend-only, no paid APIs."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings


class AIProvider(ABC):
    """Generative AI behind typed tasks. Calculations stay deterministic elsewhere."""

    @abstractmethod
    async def generate_structured(
        self,
        *,
        task: str,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError


def get_ai_provider() -> AIProvider:
    name = settings.ai_provider.lower().strip()
    if name == "ollama":
        from app.ai.ollama import OllamaAIProvider

        return OllamaAIProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
        )
    from app.ai.demo import DemoAIProvider

    return DemoAIProvider()

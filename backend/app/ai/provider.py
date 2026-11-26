"""AIProvider interface and factory."""

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings


class AIProvider(ABC):
    """Backend-only generative AI interface. No paid APIs."""

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

        return OllamaAIProvider()
    from app.ai.demo import DemoAIProvider

    return DemoAIProvider()

"""Optional Ollama adapter — local open models only; falls back to DemoAIProvider."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from app.ai.demo import DemoAIProvider
from app.ai.provider import AIProvider

logger = logging.getLogger(__name__)

_TASK_PROMPTS = {
    "service_report": (
        "Return JSON only with keys: problem, diagnosis, work_performed, parts (array of strings), "
        "follow_up. Draft a field-service report from the notes. Do not claim job completion or "
        "customer signature. Label uncertain items as suggestions."
    ),
    "job_prep": (
        "Return JSON only with keys: summary (string), suggested_checklist (array of "
        "{label, reason}), history_highlights (array of strings). Prepare a technician for the job "
        "using provided history/checklist context. Suggestions require human confirmation."
    ),
    "service_memory": (
        "Return JSON only with keys: recurring_themes (array of strings), suggested_follow_up "
        "(string). Summarize recurring failures from the provided recorded history only. "
        "Do not invent jobs that are not in context. Follow-up is a suggestion requiring confirmation."
    ),
}


class OllamaAIProvider(AIProvider):
    """
    Calls local Ollama `/api/chat` for structured JSON when reachable.
    On any failure, falls back to DemoAIProvider so demos never require Ollama.
    """

    def __init__(self, *, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._fallback = DemoAIProvider()

    async def generate_structured(
        self,
        *,
        task: str,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context or {}
        available = await self._ping()
        if not available:
            result = await self._fallback.generate_structured(
                task=task, input_text=input_text, context=context
            )
            result["provider"] = "demo-fallback"
            result["ollama_reachable"] = False
            return result

        try:
            parsed = await self._chat_json(task=task, input_text=input_text, context=context)
            parsed["provider"] = "ollama"
            parsed["ollama_reachable"] = True
            parsed["model"] = self.model
            parsed["labeled_ai"] = True
            return self._normalize(task, parsed, input_text, context)
        except Exception as exc:
            logger.warning("Ollama generation failed (%s); using demo fallback", exc)
            result = await self._fallback.generate_structured(
                task=task, input_text=input_text, context=context
            )
            result["provider"] = "demo-fallback"
            result["ollama_reachable"] = True
            result["ollama_error"] = str(exc)[:200]
            return result

    async def _ping(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    async def _chat_json(
        self,
        *,
        task: str,
        input_text: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        instruction = _TASK_PROMPTS.get(
            task,
            "Return a JSON object summarizing the request. Do not invent business facts.",
        )
        user_content = (
            f"Task: {task}\n"
            f"Input:\n{input_text}\n\n"
            f"Context JSON:\n{json.dumps(context, default=str)[:4000]}\n\n"
            f"{instruction}"
        )
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a field-service assistant. Respond with valid JSON only. "
                        "Never complete jobs, certify safety, or sign for customers."
                    ),
                },
                {"role": "user", "content": user_content},
            ],
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{self.base_url}/api/chat", json=payload)
            response.raise_for_status()
            data = response.json()
        content = (data.get("message") or {}).get("content") or data.get("response") or "{}"
        if isinstance(content, dict):
            return content
        return json.loads(content)

    def _normalize(
        self,
        task: str,
        parsed: dict[str, Any],
        input_text: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        if task == "service_report":
            return {
                "problem": str(parsed.get("problem") or ""),
                "diagnosis": str(parsed.get("diagnosis") or ""),
                "work_performed": str(parsed.get("work_performed") or ""),
                "parts": [str(p) for p in (parsed.get("parts") or [])],
                "follow_up": str(parsed.get("follow_up") or ""),
                "raw_notes_echo": input_text[:500],
                "provider": parsed.get("provider", "ollama"),
                "ollama_reachable": True,
                "model": self.model,
                "labeled_ai": True,
            }
        if task == "job_prep":
            suggestions = parsed.get("suggested_checklist") or []
            normalized = []
            for item in suggestions:
                if isinstance(item, str):
                    normalized.append(
                        {"label": item, "reason": "Ollama suggestion", "confirmed": False}
                    )
                elif isinstance(item, dict):
                    normalized.append(
                        {
                            "label": str(item.get("label") or item.get("text") or ""),
                            "reason": str(item.get("reason") or "Ollama suggestion"),
                            "confirmed": False,
                        }
                    )
            return {
                "summary": str(parsed.get("summary") or ""),
                "job_type": context.get("job_type"),
                "suggested_checklist": [s for s in normalized if s["label"]],
                "history_highlights": [
                    str(h) for h in (parsed.get("history_highlights") or context.get("history_highlights") or [])
                ],
                "existing_checklist": context.get("existing_checklist") or [],
                "provider": parsed.get("provider", "ollama"),
                "ollama_reachable": True,
                "model": self.model,
                "labeled_ai": True,
            }
        if task == "service_memory":
            themes = parsed.get("recurring_themes") or []
            if isinstance(themes, str):
                themes = [themes]
            return {
                "query": input_text,
                "recurring_themes": [str(t) for t in themes],
                "suggested_follow_up": str(parsed.get("suggested_follow_up") or ""),
                "hit_count": context.get("hit_count", 0),
                "provider": parsed.get("provider", "ollama"),
                "ollama_reachable": True,
                "model": self.model,
                "labeled_ai": True,
            }
        return parsed

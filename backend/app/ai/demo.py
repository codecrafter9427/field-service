"""Deterministic DemoAIProvider — works without Ollama."""

from typing import Any

from app.ai.provider import AIProvider


class DemoAIProvider(AIProvider):
    async def generate_structured(
        self,
        *,
        task: str,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context or {}
        if task == "service_report":
            return {
                "problem": "Demo: intermittent equipment fault reported by technician notes.",
                "diagnosis": "Demo: likely wear on primary component; inspect seals and filters.",
                "work_performed": "Demo: inspected unit, cleaned contacts, verified operation.",
                "parts": [],
                "follow_up": "Demo: schedule preventive maintenance within 30 days.",
                "raw_notes_echo": input_text[:500],
                "provider": "demo",
            }
        if task == "job_prep":
            return {
                "summary": "Demo job prep: review prior service notes and bring standard checklist.",
                "suggested_checklist": [
                    "Verify asset serial number",
                    "Confirm customer contact on site",
                    "Inspect safety shutoffs",
                ],
                "history_highlights": context.get("history", []),
                "provider": "demo",
            }
        if task == "service_memory":
            return {
                "recurring_themes": [
                    "Demo: repeated filter clogging on this asset over last 3 visits."
                ],
                "suggested_follow_up": "Demo: propose quarterly filter replacement plan.",
                "provider": "demo",
            }
        return {
            "message": "Demo AI stub — unknown task",
            "task": task,
            "provider": "demo",
        }

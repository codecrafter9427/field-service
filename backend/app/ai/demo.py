"""Deterministic DemoAIProvider — works without Ollama or any paid API."""

from __future__ import annotations

from typing import Any

from app.ai.provider import AIProvider
from app.services.checklist_templates import resolve_job_type, suggest_checklist_items


class DemoAIProvider(AIProvider):
    """Fixed, explainable stub responses grounded in provided context when present."""

    async def generate_structured(
        self,
        *,
        task: str,
        input_text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        context = context or {}
        if task == "service_report":
            return self._service_report(input_text, context)
        if task == "job_prep":
            return self._job_prep(input_text, context)
        if task == "service_memory":
            return self._service_memory(input_text, context)
        return {
            "message": "Demo AI — unknown task",
            "task": task,
            "provider": "demo",
        }

    def _service_report(self, input_text: str, context: dict[str, Any]) -> dict[str, Any]:
        notes = (input_text or "").strip()
        title = context.get("title") or "service visit"
        asset_name = context.get("asset_name") or "equipment"
        parts_used = context.get("parts_used") or []
        echo = notes[:500] if notes else f"(no notes) work order: {title}"

        problem = (
            f"Customer reported issue on {asset_name} related to: {title}."
            if not notes
            else f"From technician notes on {asset_name}: {notes[:180]}"
        )
        diagnosis = (
            "Likely wear or restriction based on recorded notes; "
            "verify seals, filters, and operating setpoints before closing."
        )
        if "filter" in notes.lower() or "filter" in title.lower():
            diagnosis = (
                "Notes mention filter/airflow — inspect filter media, "
                "measure static pressure, and confirm condensate drain clear."
            )
        if "leak" in notes.lower() or "leak" in title.lower():
            diagnosis = (
                "Notes mention leak — isolate circuit, inspect joints/gaskets, "
                "and document dye or soap-test findings."
            )

        work = (
            f"Inspected {asset_name}, addressed reported symptoms for '{title}', "
            "and verified basic operation before leaving site."
        )
        parts = [str(p) for p in parts_used] if parts_used else []
        if not parts and ("filter" in notes.lower() or "filter" in title.lower()):
            parts = ["Filter media pack (demo suggestion from notes)"]

        return {
            "problem": problem,
            "diagnosis": diagnosis,
            "work_performed": work,
            "parts": parts,
            "follow_up": (
                "Schedule preventive check within 30 days if symptoms recur; "
                "technician must edit/approve this draft before finalizing."
            ),
            "raw_notes_echo": echo,
            "provider": "demo",
            "labeled_ai": True,
        }

    def _job_prep(self, input_text: str, context: dict[str, Any]) -> dict[str, Any]:
        title = context.get("title") or input_text or "upcoming job"
        asset_name = context.get("asset_name") or "assigned asset"
        history = context.get("history_highlights") or []
        existing = context.get("existing_checklist") or []
        job_type = resolve_job_type(
            title=title,
            skill_required=context.get("skill_required"),
            asset_type=context.get("asset_type"),
            explicit=context.get("job_type"),
        )
        suggestions = [
            {"label": label, "reason": reason, "confirmed": False}
            for label, reason in suggest_checklist_items(job_type)
            if label not in existing
        ]
        summary_bits = [
            f"Prepare for '{title}' on {asset_name} (job type: {job_type}).",
        ]
        if history:
            summary_bits.append(f"Prior history highlights: {'; '.join(history[:3])}")
        else:
            summary_bits.append("No prior activity notes found for this asset/customer in scope.")
        if existing:
            summary_bits.append(f"Existing checklist already has {len(existing)} item(s).")

        return {
            "summary": " ".join(summary_bits),
            "job_type": job_type,
            "suggested_checklist": suggestions,
            "history_highlights": history,
            "existing_checklist": existing,
            "provider": "demo",
            "labeled_ai": True,
        }

    def _service_memory(self, input_text: str, context: dict[str, Any]) -> dict[str, Any]:
        themes_ctx = context.get("theme_counts") or {}
        asset_names = context.get("asset_names") or []
        customer_names = context.get("customer_names") or []
        hit_count = int(context.get("hit_count") or 0)
        titles = context.get("titles") or []

        recurring: list[str] = []
        if themes_ctx:
            for theme, count in list(themes_ctx.items())[:5]:
                scope = (
                    f"asset(s) {', '.join(asset_names[:2])}"
                    if asset_names
                    else (
                        f"customer(s) {', '.join(customer_names[:2])}"
                        if customer_names
                        else "recorded history"
                    )
                )
                recurring.append(
                    f"Repeated '{theme}' signals ({count} mentions) across {scope} "
                    f"from {hit_count} related job(s)."
                )
        elif titles:
            recurring.append(
                f"Related jobs in history: {', '.join(titles[:4])}. "
                "No strong keyword theme extracted — review source jobs manually."
            )
        else:
            recurring.append(
                "No matching service history for this query/asset/customer in the organization."
            )

        if "filter" in themes_ctx:
            follow = (
                "Propose a quarterly filter replacement / airflow PM plan "
                "based on recorded filter-related visits (confirm before creating work)."
            )
        elif "leak" in themes_ctx or "refrigerant" in themes_ctx or "gasket" in themes_ctx:
            follow = (
                "Propose a sealed-system / gasket inspection follow-up "
                "from recorded leak/seal history (confirm before creating work)."
            )
        elif hit_count > 0:
            follow = (
                f"Review the {hit_count} source job(s) and confirm a preventive "
                "maintenance follow-up if the pattern continues."
            )
        else:
            follow = "No maintenance follow-up suggested — expand search or pick an asset/customer."

        query = input_text or context.get("query") or ""
        return {
            "query": query,
            "recurring_themes": recurring,
            "suggested_follow_up": follow,
            "hit_count": hit_count,
            "provider": "demo",
            "labeled_ai": True,
        }

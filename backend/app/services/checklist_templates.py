"""Deterministic checklist suggestions by job type — AI may recommend; tech confirms."""

from __future__ import annotations

# Allowlisted suggestions keyed by job-type keywords (title / skill / asset_type).
CHECKLIST_BY_JOB_TYPE: dict[str, list[tuple[str, str]]] = {
    "hvac": [
        ("Verify filter condition and size", "HVAC jobs often involve airflow restriction"),
        ("Check condensate drain line", "Common HVAC failure point"),
        ("Confirm thermostat setpoints with customer", "Avoid callback for comfort complaints"),
        ("Record supply/return temps", "Document baseline for Service Memory"),
    ],
    "refrigeration": [
        ("Check evaporator coil frost pattern", "Diagnose airflow vs charge issues"),
        ("Inspect door gaskets for seal", "Common cold-loss cause"),
        ("Verify condenser cleanliness", "Heat rejection failures recur"),
        ("Log box temperature before/after", "Evidence for recurring leak patterns"),
    ],
    "plumbing": [
        ("Isolate water supply before opening lines", "Safety and containment"),
        ("Inspect seals and unions for weeps", "Recurring leak detection"),
        ("Confirm drainage slope / trap seal", "Prevent callback odor/flood issues"),
    ],
    "electrical": [
        ("Lockout/tagout confirmed", "Safety gate before energizing work"),
        ("Verify voltage at source", "Rule out supply-side faults"),
        ("Inspect connections for heat discoloration", "Recurring loose-connection failures"),
    ],
    "elevator": [
        ("Place car out of service with signage", "Public safety"),
        ("Test call buttons on each floor", "Intermittent call complaints"),
        ("Document fault codes from controller", "Service Memory recurrence tracking"),
    ],
    "medical": [
        ("Confirm device idle / cooldown complete", "Protect equipment and staff"),
        ("Log cycle fault codes", "Recurring sterilizer/cooler patterns"),
        ("Sanitize contact surfaces after service", "Site hygiene requirement"),
    ],
    "kitchen": [
        ("Power down and cool appliance", "Burn/scald prevention"),
        ("Descale pathway inspection", "Recurring scale buildup"),
        ("Verify water filter date", "Taste/pressure callbacks"),
    ],
    "general": [
        ("Verify asset serial number", "Match work order to equipment"),
        ("Confirm customer contact on site", "Access and signoff readiness"),
        ("Inspect safety shutoffs", "Baseline safety before work"),
        ("Photograph before/after condition", "Evidence for report"),
    ],
}


def resolve_job_type(
    *,
    title: str | None = None,
    skill_required: str | None = None,
    asset_type: str | None = None,
    explicit: str | None = None,
) -> str:
    if explicit:
        key = explicit.strip().lower()
        if key in CHECKLIST_BY_JOB_TYPE:
            return key
    blob = " ".join(
        p for p in (title or "", skill_required or "", asset_type or "") if p
    ).lower()
    for key in (
        "hvac",
        "refrigeration",
        "plumbing",
        "electrical",
        "elevator",
        "medical",
        "kitchen",
    ):
        if key in blob:
            return key
    if "cooler" in blob or "freezer" in blob or "refriger" in blob:
        return "refrigeration"
    if "boiler" in blob or "pump" in blob or "plumb" in blob:
        return "plumbing"
    if "generator" in blob or "power" in blob or "thermostat" in blob:
        return "electrical"
    if "steriliz" in blob or "x-ray" in blob:
        return "medical"
    if "espresso" in blob or "kitchen" in blob:
        return "kitchen"
    if "elevator" in blob or "lift" in blob:
        return "elevator"
    return "general"


def suggest_checklist_items(job_type: str) -> list[tuple[str, str]]:
    return list(CHECKLIST_BY_JOB_TYPE.get(job_type, CHECKLIST_BY_JOB_TYPE["general"]))

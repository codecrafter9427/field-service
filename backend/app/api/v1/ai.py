"""AI endpoint stubs — DemoAIProvider / Ollama adapter only."""

from fastapi import APIRouter

from app.ai import get_ai_provider
from app.schemas.common import AIRequest, AIResponse, AISource

router = APIRouter()


@router.post("/service-report", response_model=AIResponse)
async def service_report(body: AIRequest) -> AIResponse:
    provider = get_ai_provider()
    result = await provider.generate_structured(
        task="service_report",
        input_text=body.input,
        context={"context_ids": body.context_ids, **body.options},
    )
    return AIResponse(
        result=result,
        explanation="Stub service report. Review and edit before attaching. AI cannot complete the job.",
        sources=[
            AISource(type="context", id=cid, label=f"context:{cid}")
            for cid in body.context_ids
        ],
        requires_confirmation=True,
    )


@router.post("/job-prep", response_model=AIResponse)
async def job_prep(body: AIRequest) -> AIResponse:
    provider = get_ai_provider()
    result = await provider.generate_structured(
        task="job_prep",
        input_text=body.input,
        context={"context_ids": body.context_ids, **body.options},
    )
    return AIResponse(
        result=result,
        explanation="Stub job prep summary from provided context ids only.",
        sources=[
            AISource(type="context", id=cid, label=f"context:{cid}")
            for cid in body.context_ids
        ],
        requires_confirmation=True,
    )


@router.post("/service-memory", response_model=AIResponse)
async def service_memory(body: AIRequest) -> AIResponse:
    """Differentiator stub — Service Memory (not fully implemented)."""
    provider = get_ai_provider()
    result = await provider.generate_structured(
        task="service_memory",
        input_text=body.input,
        context={"context_ids": body.context_ids, **body.options},
    )
    return AIResponse(
        result=result,
        explanation=(
            "Service Memory stub: recurring-failure search/summary is backlog. "
            "Demo output only; confirm before creating follow-up work."
        ),
        sources=[
            AISource(type="context", id=cid, label=f"context:{cid}")
            for cid in body.context_ids
        ],
        requires_confirmation=True,
    )

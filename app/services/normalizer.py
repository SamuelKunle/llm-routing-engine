from typing import List

from app.schemas.chat import ChatResponse, ProviderResult


def normalize_result(
    result: ProviderResult,
    attempted_providers: List[str],
    fallback_used: bool,
) -> ChatResponse:
    return ChatResponse(
        success=True,
        message=result.output_text,
        provider_used=result.provider,
        model_used=result.model,
        fallback_used=fallback_used,
        metadata={
            "latency_ms": result.latency_ms,
            "attempted_providers": attempted_providers,
        },
    )

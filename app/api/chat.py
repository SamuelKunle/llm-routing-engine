from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatRequest, ChatResponse, HealthResponse
from app.services.router import LLMRouter
from app.utils.errors import ProviderError

router = APIRouter()
llm_router = LLMRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", available_providers=llm_router.get_available_provider_names())


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await llm_router.generate(request)
    except ProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=8000)
    preferred_provider: Optional[str] = Field(default=None, description="openai, anthropic, or mock")
    allow_fallback: bool = Field(default=True)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_tokens: int = Field(default=300, ge=1, le=4000)


class ChatResponse(BaseModel):
    success: bool
    message: str
    provider_used: str
    model_used: str
    fallback_used: bool
    metadata: Dict[str, Any]


class ProviderResult(BaseModel):
    provider: str
    model: str
    output_text: str
    raw: Dict[str, Any]
    latency_ms: int


class HealthResponse(BaseModel):
    status: str
    available_providers: List[str]

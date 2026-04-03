import time

import httpx

from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ProviderResult
from app.services.providers.base import BaseProvider
from app.utils.errors import ProviderConfigurationError, ProviderError


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    async def generate(self, request: ChatRequest) -> ProviderResult:
        settings = get_settings()
        if not settings.anthropic_api_key:
            raise ProviderConfigurationError("ANTHROPIC_API_KEY is not configured")

        started = time.perf_counter()
        url = f"{settings.anthropic_base_url.rstrip('/')}/messages"
        headers = {
            "x-api-key": settings.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": settings.anthropic_model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.message}],
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"Anthropic provider failed: {exc}") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        try:
            output_text = "\n".join(block["text"] for block in data["content"] if block.get("type") == "text")
        except (KeyError, TypeError) as exc:
            raise ProviderError("Anthropic response format was unexpected") from exc

        return ProviderResult(
            provider=self.name,
            model=settings.anthropic_model,
            output_text=output_text,
            raw=data,
            latency_ms=latency_ms,
        )

import time

import httpx

from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ProviderResult
from app.services.providers.base import BaseProvider
from app.utils.errors import ProviderConfigurationError, ProviderError


class OpenAIProvider(BaseProvider):
    name = "openai"

    async def generate(self, request: ChatRequest) -> ProviderResult:
        settings = get_settings()
        if not settings.openai_api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY is not configured")

        started = time.perf_counter()
        url = f"{settings.openai_base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.openai_model,
            "messages": [{"role": "user", "content": request.message}],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            raise ProviderError(f"OpenAI provider failed: {exc}") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        try:
            output_text = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenAI response format was unexpected") from exc

        return ProviderResult(
            provider=self.name,
            model=settings.openai_model,
            output_text=output_text,
            raw=data,
            latency_ms=latency_ms,
        )

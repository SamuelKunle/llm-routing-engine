import pytest

from app.schemas.chat import ChatRequest
from app.services.providers.base import BaseProvider
from app.services.router import LLMRouter
from app.schemas.chat import ProviderResult
from app.utils.errors import ProviderError


class FailingProvider(BaseProvider):
    name = "failing"

    async def generate(self, request: ChatRequest) -> ProviderResult:
        raise ProviderError("Intentional failure")


class SuccessProvider(BaseProvider):
    name = "success"

    async def generate(self, request: ChatRequest) -> ProviderResult:
        return ProviderResult(
            provider=self.name,
            model="success-model",
            output_text="Recovered through fallback",
            raw={},
            latency_ms=5,
        )


@pytest.mark.asyncio
async def test_router_falls_back_when_first_provider_fails():
    router = LLMRouter()
    router.providers = {
        "failing": FailingProvider(),
        "success": SuccessProvider(),
    }
    router.settings.default_provider = "failing"
    router.settings.fallback_providers = "success"

    result = await router.generate(
        ChatRequest(message="hello", preferred_provider="failing", allow_fallback=True)
    )

    assert result.success is True
    assert result.provider_used == "success"
    assert result.fallback_used is True
    assert result.metadata["attempted_providers"] == ["failing", "success"]

import time

from app.schemas.chat import ChatRequest, ProviderResult
from app.services.providers.base import BaseProvider


class MockProvider(BaseProvider):
    name = "mock"

    async def generate(self, request: ChatRequest) -> ProviderResult:
        started = time.perf_counter()
        text = f"Mock reply: {request.message}"
        latency_ms = int((time.perf_counter() - started) * 1000) + 12
        return ProviderResult(
            provider=self.name,
            model="mock-default",
            output_text=text,
            raw={"mock": True},
            latency_ms=latency_ms,
        )

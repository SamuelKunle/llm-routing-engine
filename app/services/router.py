import logging
from typing import Dict, List

from app.core.config import get_settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.normalizer import normalize_result
from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.base import BaseProvider
from app.services.providers.mock_provider import MockProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.utils.errors import ProviderError

logger = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.providers: Dict[str, BaseProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "mock": MockProvider(),
        }

    def get_available_provider_names(self) -> List[str]:
        return list(self.providers.keys())

    def _build_provider_order(self, preferred_provider: str | None, allow_fallback: bool) -> List[str]:
        initial = preferred_provider or self.settings.default_provider
        order: List[str] = [initial]

        if allow_fallback:
            for provider in self.settings.fallback_provider_list:
                if provider not in order:
                    order.append(provider)

        return [provider for provider in order if provider in self.providers]

    async def generate(self, request: ChatRequest) -> ChatResponse:
        provider_order = self._build_provider_order(request.preferred_provider, request.allow_fallback)
        attempted: List[str] = []
        last_error: str | None = None

        for index, provider_name in enumerate(provider_order):
            attempted.append(provider_name)
            provider = self.providers[provider_name]
            try:
                result = await provider.generate(request)
                return normalize_result(
                    result=result,
                    attempted_providers=attempted,
                    fallback_used=index > 0,
                )
            except ProviderError as exc:
                last_error = str(exc)
                logger.warning("Provider %s failed: %s", provider_name, exc)
                continue

        raise ProviderError(last_error or "No provider could process the request")

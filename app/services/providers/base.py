from abc import ABC, abstractmethod

from app.schemas.chat import ChatRequest, ProviderResult


class BaseProvider(ABC):
    name: str

    @abstractmethod
    async def generate(self, request: ChatRequest) -> ProviderResult:
        raise NotImplementedError

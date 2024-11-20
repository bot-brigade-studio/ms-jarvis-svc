# llm/base.py

from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Optional, AsyncIterator
from core.types import LLMConfig, LLMResponse, ConversationHistory, StreamChunk

class BaseLLMProvider(ABC):
    def __init__(self, config: LLMConfig):
        self.config = config

    @abstractmethod
    async def generate(
        self,
        system_prompt: Optional[str],
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        system_prompt: Optional[str],
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> AsyncIterator[StreamChunk]:
        pass

    async def _handle_stream_callback(
        self,
        chunk: StreamChunk,
        callback: Optional[Callable[[StreamChunk], Awaitable[None]]] = None
    ) -> None:
        if callback:
            await callback(chunk)
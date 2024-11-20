# llm/base.py
from abc import ABC, abstractmethod
from typing import Optional
from core.types import LLMConfig, LLMResponse, ConversationHistory

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
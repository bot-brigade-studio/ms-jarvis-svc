from typing import Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from .base import BaseLLMProvider
from ..core.types import ConversationHistory, LLMResponse, LLMConfig
from ..core.exceptions import LLMProviderError
from ..core.logging import log_llm_request, log_error

class OpenAIProvider(BaseLLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=config.api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        system_prompt: str,
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Convert conversation history to messages
            for msg in conversation.messages:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })

            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens
            )

            log_llm_request(
                provider="openai",
                model=self.config.model,
                tokens=response.usage.total_tokens
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                metadata={
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                }
            )

        except Exception as e:
            log_error(e, {"provider": "openai", "model": self.config.model})
            raise LLMProviderError(f"OpenAI API error: {str(e)}")
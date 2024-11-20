# llm/anthropic.py
from anthropic import AsyncAnthropic
from typing import Dict, List, Optional

from core.exceptions import LLMProviderError
from core.logging import log_llm_request
from core.types import ConversationHistory, LLMConfig, LLMResponse, MessageRole
from llm.base import BaseLLMProvider

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncAnthropic(api_key=config.api_key)
        
    def _convert_messages(self, conversation: ConversationHistory) -> List[Dict[str, str]]:
        messages = []
        
        # Convert conversation history
        for msg in conversation.messages:
            messages.append({
                "role": msg.role.value,
                "content": msg.content
            })
            
        return messages

    async def generate(
        self,
        system_prompt: Optional[str],
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> LLMResponse:
        try:
            messages = self._convert_messages(conversation)
            
            response = await self.client.messages.create(
                model=self.config.model,
                system=system_prompt,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens or 4096
            )
            additional_kwargs = {
                "messages": messages,
                "system_prompt": system_prompt,
                "response": response.content[0].text
            }
            log_llm_request(
                provider="anthropic",
                model=self.config.model,
                tokens=response.usage.output_tokens,
                **additional_kwargs
            )

            return LLMResponse(
                content=response.content[0].text,
                metadata={"provider": "anthropic"}
            )

        except Exception as e:
            raise LLMProviderError(f"Anthropic API error: {str(e)}")
# llm/anthropic.py
from anthropic import AsyncAnthropic
from typing import AsyncIterator, Dict, List, Optional

from chainable_llm.core.exceptions import LLMProviderError
from chainable_llm.core.logging import log_llm_request, log_any
from chainable_llm.core.streaming import StreamBuffer
from chainable_llm.core.types import (
    ConversationHistory,
    LLMConfig,
    LLMResponse,
    StreamChunk,
)
from chainable_llm.llm.base import BaseLLMProvider


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.api_key = config.api_key if not config.proxy_enabled else config.proxy_api_key
        self.base_url = config.proxy_url if config.proxy_enabled else None
        self.client = AsyncAnthropic(
            api_key=self.api_key,
            base_url=self.base_url,
        )
        
    def _convert_messages(
        self, conversation: ConversationHistory
    ) -> List[Dict[str, str]]:
        messages = []

        # Convert conversation history
        for msg in conversation.messages:
            messages.append({"role": msg.role.value, "content": msg.content})

        return messages

    async def generate(
        self,
        system_prompt: Optional[str],
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        try:
            messages = self._convert_messages(conversation)

            response = await self.client.messages.create(
                model=self.config.model,
                system=system_prompt,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens or 4096,
            )
            additional_kwargs = {
                "messages": messages,
                "system_prompt": system_prompt,
                "response": response.content[0].text,
            }
            log_llm_request(
                provider="anthropic",
                model=self.config.model,
                tokens=response.usage.output_tokens,
                **additional_kwargs,
            )

            return LLMResponse(
                content=response.content[0].text, metadata={"provider": "anthropic"}
            )

        except Exception as e:
            raise LLMProviderError(f"Anthropic API error: {str(e)}")

    async def generate_stream(
        self,
        system_prompt: Optional[str],
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        try:
            messages = self._convert_messages(conversation)

            message_exclude_system = [m for m in messages if m["role"] != "system"]

            log_any(
                message="Generating stream with Anthropic",
                **{
                    "model": self.config.model,
                    "system_prompt": system_prompt,
                    "messages": message_exclude_system,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            stream = await self.client.messages.create(
                model=self.config.model,
                system=system_prompt,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens or 4096,
                stream=True,
            )

            buffer = StreamBuffer(self.config.streaming)
            prompt_tokens = 0
            completion_tokens = 0
            async for chunk in stream:
                if chunk.type == "message_start":
                    prompt_tokens = chunk.message.usage.input_tokens
                    completion_tokens = chunk.message.usage.output_tokens
                elif chunk.type == "content_block_delta":
                    content = chunk.delta.text or " "
                    stream_chunk = await buffer.process_chunk(content, done=False)
                    if stream_chunk:
                        yield stream_chunk
                elif chunk.type == "message_delta":
                    completion_tokens += chunk.usage.output_tokens

            # Handle final chunk
            final_chunk = await buffer.process_chunk(
                " ",
                done=True,
                metadata={
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                    }
                },
            )
            if final_chunk:
                yield final_chunk

        except Exception as e:
            raise LLMProviderError(f"Anthropic streaming error: {str(e)}")

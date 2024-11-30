from typing import AsyncIterator, Optional
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from chainable_llm.core.streaming import StreamBuffer
from chainable_llm.llm.base import BaseLLMProvider
from chainable_llm.core.types import (
    ConversationHistory,
    LLMResponse,
    LLMConfig,
    StreamChunk,
)
from chainable_llm.core.exceptions import LLMProviderError
from chainable_llm.core.logging import (
    log_llm_request,
    log_error,
    log_stream_chunk,
    log_any,
)


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = AsyncOpenAI(api_key=config.api_key)

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate(
        self,
        system_prompt: str,
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Convert conversation history to messages
            for msg in conversation.messages:
                messages.append({"role": msg.role.value, "content": msg.content})

            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
            )

            additional_kwargs = {
                "messages": messages,
                # "system_prompt": system_prompt,
                "response": response.choices[0].message.content,
            }
            log_llm_request(
                provider="openai",
                model=self.config.model,
                tokens=response.usage.total_tokens,
                **additional_kwargs,
            )

            return LLMResponse(
                content=response.choices[0].message.content,
                metadata={
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens,
                    }
                },
            )

        except Exception as e:
            log_error(e, {"provider": "openai", "model": self.config.model})
            raise LLMProviderError(f"OpenAI API error: {str(e)}")

    async def generate_stream(
        self,
        system_prompt: Optional[str],
        conversation: ConversationHistory,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[StreamChunk]:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Convert conversation history
            for msg in conversation.messages:
                messages.append({"role": msg.role.value, "content": msg.content})

            message_exclude_system = [m for m in messages if m["role"] != "system"]

            log_any(
                message="Generating stream with OpenAI",
                **{
                    "model": self.config.model,
                    "system_prompt": system_prompt,
                    "messages": message_exclude_system,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )

            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=temperature or self.config.temperature,
                max_tokens=max_tokens or self.config.max_tokens,
                stream=True,
            )

            buffer = StreamBuffer(self.config.streaming)

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    stream_chunk = await buffer.process_chunk(content, done=False)

                    if stream_chunk:
                        log_stream_chunk(
                            provider="openai",
                            chunk_size=len(stream_chunk.content),
                            is_final=False,
                        )
                        yield stream_chunk

            # Handle final chunk
            final_chunk = await buffer.process_chunk("", done=True)
            if final_chunk:
                log_stream_chunk(
                    provider="openai",
                    chunk_size=len(final_chunk.content),
                    is_final=True,
                )
                yield final_chunk

        except Exception as e:
            log_error(e, {"provider": "openai", "model": self.config.model})
            raise LLMProviderError(f"OpenAI streaming error: {str(e)}")

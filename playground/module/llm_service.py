from typing import List, Optional, Dict, AsyncIterator
from fastapi import HTTPException
import anthropic
import openai
from enum import Enum
import async_timeout


class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class StreamResponse:
    def __init__(
        self,
        content: str,
        index: int,
        is_final: bool = False,
        finish_reason: Optional[str] = None,
    ):
        self.content = content
        self.index = index
        self.is_final = is_final
        self.finish_reason = finish_reason


class ModelConfig:
    def __init__(
        self,
        provider: ProviderType,
        model_name: str,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens


class LLMService:
    def __init__(self, anthropic_api_key: str, openai_api_key: str):
        self.anthropic_client = anthropic.AsyncClient(api_key=anthropic_api_key)
        self.openai_client = openai.AsyncClient(api_key=openai_api_key)

        self.model_configs = {
            "claude-3-5-sonnet-20241022": ModelConfig(
                temperature=0.7,
                max_tokens=4096,
                model_name="claude-3-5-sonnet-20241022",
                provider=ProviderType.ANTHROPIC,
            ),
            "gpt-4o-mini": ModelConfig(
                temperature=0.7,
                max_tokens=4096,
                model_name="gpt-4o-mini",
                provider=ProviderType.OPENAI,
            ),
        }

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response using either Anthropic or OpenAI model
        """
        try:
            config = self.model_configs[model_name]

            if config.provider == ProviderType.ANTHROPIC:
                return await self._generate_anthropic_response(
                    messages, config, system_prompt, temperature, max_tokens
                )
            else:
                return await self._generate_openai_response(
                    messages, config, system_prompt, temperature, max_tokens
                )

        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    async def _generate_anthropic_response(
        self,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate response using Anthropic's Claude
        """
        async with async_timeout.timeout(30):
            response = await self.anthropic_client.messages.create(
                model=config.model_name,
                messages=messages,
                system=system_prompt,
                temperature=temperature or config.temperature,
                max_tokens=max_tokens or config.max_tokens,
            )
            return response.content[0].text

    async def _generate_openai_response(
        self,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate response using OpenAI's GPT
        """
        # Add system message if provided
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        async with async_timeout.timeout(30):
            response = await self.openai_client.chat.completions.create(
                model=config.model_name,
                messages=formatted_messages,
                temperature=temperature or config.temperature,
                max_tokens=max_tokens or config.max_tokens,
            )
            return response.choices[0].message.content

    async def generate_stream(
        self,
        messages: List[Dict[str, str]],
        model_name: str,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[StreamResponse]:
        """
        Stream responses from the model
        """
        config = self.model_configs[model_name]

        try:
            if config.provider == ProviderType.ANTHROPIC:
                async for chunk in self._stream_anthropic_response(
                    messages, config, system_prompt
                ):
                    yield chunk
            else:
                async for chunk in self._stream_openai_response(
                    messages, config, system_prompt
                ):
                    yield chunk

        except Exception as e:
            yield StreamResponse(content=f"Error: {str(e)}", index=-1, is_final=True)

    async def _stream_anthropic_response(
        self,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[StreamResponse]:
        try:
            stream = await self.anthropic_client.messages.create(
                model=config.model_name,
                messages=messages,
                system=system_prompt,
                max_tokens=config.max_tokens,
                stream=True,
            )

            index = 0
            async for chunk in stream:
                if chunk.type == "content_block_delta":
                    yield StreamResponse(content=chunk.delta.text, index=index)
                    index += 1

            # Final response moved outside the loop
            yield StreamResponse(content="", index=index, is_final=True)

        except Exception as e:
            yield StreamResponse(content=f"Error: {str(e)}", index=-1, is_final=True)

    async def _stream_openai_response(
        self,
        messages: List[Dict[str, str]],
        config: ModelConfig,
        system_prompt: Optional[str] = None,
    ) -> AsyncIterator[StreamResponse]:
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        formatted_messages.extend(messages)

        stream = await self.openai_client.chat.completions.create(
            model=config.model_name,
            messages=formatted_messages,
            max_tokens=config.max_tokens,
            stream=True,
        )

        index = 0
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield StreamResponse(
                    content=chunk.choices[0].delta.content, index=index
                )
                index += 1

        yield StreamResponse(content="", index=index, is_final=True)

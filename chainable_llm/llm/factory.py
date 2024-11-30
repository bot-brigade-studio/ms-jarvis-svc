from typing import Dict, Type
from chainable_llm.llm.base import BaseLLMProvider
from chainable_llm.llm.openai import OpenAIProvider
from chainable_llm.llm.anthropic import AnthropicProvider
from chainable_llm.core.types import LLMConfig
from chainable_llm.core.exceptions import ChainConfigError


class LLMFactory:
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMProvider:
        provider_class = cls._providers.get(config.provider.lower())
        if not provider_class:
            raise ChainConfigError(f"Unknown LLM provider: {config.provider}")
        return provider_class(config)

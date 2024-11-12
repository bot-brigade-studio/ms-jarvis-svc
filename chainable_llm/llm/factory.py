from typing import Dict, Type
from .base import BaseLLMProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from ..core.types import LLMConfig
from ..core.exceptions import ChainConfigError

class LLMFactory:
    _providers: Dict[str, Type[BaseLLMProvider]] = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider
    }

    @classmethod
    def create(cls, config: LLMConfig) -> BaseLLMProvider:
        provider_class = cls._providers.get(config.provider.lower())
        if not provider_class:
            raise ChainConfigError(f"Unknown LLM provider: {config.provider}")
        return provider_class(config)
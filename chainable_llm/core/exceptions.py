class ChainableLLMError(Exception):
    """Base exception for all chainable LLM errors"""

    pass


class LLMProviderError(ChainableLLMError):
    """Errors from LLM providers"""

    pass


class TransformerError(ChainableLLMError):
    """Errors in data transformation"""

    pass


class ChainConfigError(ChainableLLMError):
    """Errors in chain configuration"""

    pass

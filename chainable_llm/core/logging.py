import structlog
from typing import Any

logger = structlog.get_logger()

def log_error(error: Exception, context: dict[str, Any] = None):
    logger.error(
        "error_occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        **context or {}
    )

def log_llm_request(provider: str, model: str, tokens: int):
    logger.info(
        "llm_request",
        provider=provider,
        model=model,
        tokens=tokens
    )
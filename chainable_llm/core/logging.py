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


def log_llm_request(provider: str, model: str, tokens: int, **kwargs):
    logger.info("llm_request", provider=provider, model=model, tokens=tokens, **kwargs)


def log_any(message: str, **kwargs):
    logger.info(message, **kwargs)


def log_stream_chunk(provider: str, chunk_size: int, is_final: bool, **kwargs):
    pass
    # logger.debug(
    #     "stream_chunk_processed",
    #     provider=provider,
    #     chunk_size=chunk_size,
    #     is_final=is_final,
    #     **kwargs
    # )

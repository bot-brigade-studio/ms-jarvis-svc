# core/streaming.py
from typing import AsyncIterator, List, Optional, Dict, Any
from chainable_llm.core.types import StreamChunk, StreamConfig
from chainable_llm.core.exceptions import ChainableLLMError
from chainable_llm.core.logging import logger


class StreamBufferError(ChainableLLMError):
    """Errors specific to stream buffer operations"""

    pass


class StreamBuffer:
    def __init__(self, config: StreamConfig):
        """
        Initialize a new StreamBuffer instance.

        Args:
            config (StreamConfig): Configuration for streaming behavior
        """
        self.config = config
        self.buffer: List[str] = []
        self.total_content: List[str] = []
        self._chunk_count: int = 0
        self._total_tokens: int = 0

    @property
    def total_chunks(self) -> int:
        """Return the total number of chunks processed"""
        return self._chunk_count

    @property
    def complete_content(self) -> str:
        """Return the complete content accumulated so far"""
        return "".join(self.total_content)

    @property
    def buffer_size(self) -> int:
        """Return current buffer size in characters"""
        return len("".join(self.buffer))

    def _should_flush(self, done: bool = False) -> bool:
        """
        Determine if the buffer should be flushed based on size or completion.

        Args:
            done (bool): Whether this is the final chunk
        """
        return self.buffer_size >= self.config.chunk_size or (
            done and self.buffer_size > 0
        )

    def _create_chunk_metadata(self, done: bool) -> Dict[str, Any]:
        """
        Create metadata for the current chunk.

        Args:
            done (bool): Whether this is the final chunk
        """
        return {
            "chunk_index": self._chunk_count,
            "total_length": len(self.complete_content),
            "buffer_size": self.buffer_size,
            "is_final": done,
        }

    async def process_chunk(
        self, content: str, done: bool = False
    ) -> Optional[StreamChunk]:
        """
        Process an incoming content chunk and potentially return a StreamChunk.

        Args:
            content (str): The content to process
            done (bool): Whether this is the final chunk

        Returns:
            Optional[StreamChunk]: A chunk if buffer should be flushed, None otherwise

        Raises:
            StreamBufferError: If buffer size exceeds maximum or other processing errors
        """
        try:
            # Validate buffer size
            if self.buffer_size + len(content) > self.config.buffer_size:
                raise StreamBufferError(
                    f"Buffer size would exceed maximum of {self.config.buffer_size} characters"
                )

            # Add content to buffers
            if content:
                self.buffer.append(content)
                self.total_content.append(content)

            # Check if we should create a chunk
            if self._should_flush(done):
                self._chunk_count += 1
                chunk_content = "".join(self.buffer)
                self.buffer = []  # Clear buffer

                # Create and return chunk
                chunk = StreamChunk(
                    content=chunk_content,
                    done=done,
                    metadata=self._create_chunk_metadata(done),
                )

                # Log chunk creation
                # logger.debug(
                #     "stream_chunk_created",
                #     chunk_size=len(chunk_content),
                #     chunk_index=self._chunk_count,
                #     is_final=done,
                # )

                # Handle callback if configured
                if self.config.callback:
                    try:
                        await self.config.callback(chunk)
                    except Exception as e:
                        logger.error(
                            "stream_callback_error",
                            error=str(e),
                            chunk_index=self._chunk_count,
                        )
                        # Don't raise - callback errors shouldn't stop streaming

                return chunk

            return None

        except Exception as e:
            raise StreamBufferError(f"Error processing stream chunk: {str(e)}")

    async def flush(self) -> Optional[StreamChunk]:
        """
        Flush any remaining content in the buffer.

        Returns:
            Optional[StreamChunk]: Final chunk if buffer has content, None otherwise
        """
        if self.buffer_size > 0:
            return await self.process_chunk("", done=True)
        return None

    def reset(self) -> None:
        """Reset the buffer to initial state"""
        self.buffer = []
        self.total_content = []
        self._chunk_count = 0
        self._total_tokens = 0

    async def __aiter__(self) -> AsyncIterator[StreamChunk]:
        """
        Make StreamBuffer iterable to support async for loops.
        Yields accumulated chunks and flushes buffer at the end.
        """
        while True:
            chunk = await self.flush()
            if not chunk:
                break
            yield chunk

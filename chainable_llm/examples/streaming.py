# examples/streaming.py

# how to start:
# python -m examples.streaming

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
from core.types import (
    LLMConfig, 
    PromptConfig, 
    InputType,
    StreamConfig,
    StreamChunk
)
from nodes.base import LLMNode

async def stream_callback(chunk: StreamChunk):
    """Example callback to handle streaming chunks"""
    print(f"Received chunk: {chunk.content}", end="", flush=True)
    if chunk.done:
        print("\n--- Stream completed ---")

async def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        raise ValueError("Missing API key in environment variables")

    # Create a streaming-enabled node
    streaming_node = LLMNode(
        name="streamer",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-4o-mini",
            streaming=StreamConfig(
                enabled=True,
                chunk_size=10,
                buffer_size=1024
            )
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="You are a helpful assistant.",
            template="Explain this topic in detail: {input}"
        ),
        stream_callback=stream_callback
    )

    # Test input
    test_input = "Explain the concept of quantum entanglement"

    print(f"\nProcessing: {test_input}\n")
    
    # Process with streaming
    async for chunk in streaming_node.process_stream(test_input):
        print(f"Received chunk: {chunk.content}", end="", flush=True)
        # Additional processing can be done here if needed
        pass

if __name__ == "__main__":
    asyncio.run(main())
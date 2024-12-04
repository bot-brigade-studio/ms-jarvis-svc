# examples/streaming.py

# how to start:
# python -m examples.streaming

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
from chainable_llm.core.types import (
    LLMConfig,
    PromptConfig,
    InputType,
    StreamConfig,
    StreamChunk,
)
from chainable_llm.nodes.base import LLMNode


async def stream_callback(chunk: StreamChunk):
    """Example callback to handle streaming chunks"""
    print(f"{chunk.content}", end="", flush=True)
    if chunk.done:
        print("\n--- Stream completed ---")
        print(f"metadata: {chunk.metadata['usage']}")


async def main():
    load_dotenv()
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    proxy_api_key = os.getenv("BBPROXY_API_KEY")
    bbproxy_enabled = os.getenv("BBPROXY_IS_ENABLED")
    bbproxy_llm_url = os.getenv("BBPROXY_LLM_URL")
    

    if not openai_api_key and not anthropic_api_key:
        raise ValueError("Missing API key in environment variables")

    # Create a streaming-enabled node
    streaming_node_openai = LLMNode(
        name="streamer_openai",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            proxy_api_key=proxy_api_key,
            proxy_enabled=bbproxy_enabled,
            proxy_url=bbproxy_llm_url,
            model="gpt-4o-mini",
            streaming=StreamConfig(enabled=True, chunk_size=10),
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="You are a helpful assistant.",
            template="Explain this topic with short sentences: {input}",
        ),
        stream_callback=stream_callback,
    )
    streaming_node_anthropic = LLMNode(
        name="streamer_anthropic",
        llm_config=LLMConfig(
            provider="anthropic",
            api_key=anthropic_api_key,
            proxy_api_key=proxy_api_key,
            proxy_enabled=True,
            proxy_url=bbproxy_llm_url,
            model="claude-3-5-sonnet-20240620",
            streaming=StreamConfig(enabled=True, chunk_size=10),
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="You are a helpful assistant.",
            template="Explain this topic with short sentences: {input}",
        ),
        stream_callback=stream_callback,
    )

    # Test input
    test_input = "Explain the concept of quantum entanglement"

    print(f"\nProcessing: {test_input}\n")
    
    # result = await streaming_node.process(test_input)
    # print("result.content", result.content)
    # print("result.metadata", result.metadata)

    # Process with streaming
    # async for chunk in streaming_node_openai.process_stream(test_input):
    #     pass
    
    async for chunk in streaming_node_anthropic.process_stream(test_input):
        pass


if __name__ == "__main__":
    asyncio.run(main())

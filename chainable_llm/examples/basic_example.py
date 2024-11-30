# examples/smart_routing.py

import asyncio
import os
from dotenv import load_dotenv
from chainable_llm.core.types import (
    LLMConfig,
    PromptConfig,
    InputType,
)
from chainable_llm.nodes.base import LLMNode


# Example usage with different prompt types
async def main():
    load_dotenv()
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    openai_api_key = os.getenv("OPENAI_API_KEY")

    if not openai_api_key or not anthropic_api_key:
        raise ValueError("Missing API keys in environment variables")
    # System prompt example
    system_node = LLMNode(
        llm_config=LLMConfig(
            provider="openai", api_key=openai_api_key, model="gpt-4o-mini"
        ),
        prompt_config=PromptConfig(
            input_type=InputType.SYSTEM_PROMPT,
            template="You are an expert in {input}. Provide detailed analysis.",
        ),
    )

    # User prompt example
    user_node = LLMNode(
        llm_config=LLMConfig(
            provider="anthropic",
            api_key=anthropic_api_key,
            model="claude-3-5-sonnet-20240620",
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="You are a helpful assistant.",
            template="Please analyze this topic: {input}",
        ),
    )

    # Append system example
    append_node = LLMNode(
        llm_config=LLMConfig(
            provider="openai", api_key=openai_api_key, model="gpt-4o-mini"
        ),
        prompt_config=PromptConfig(
            input_type=InputType.APPEND_SYSTEM,
            base_system_prompt="You are a helpful assistant.",
            template="Additionally, you have expertise in {input}.",
        ),
    )

    # Test the nodes
    result1 = await system_node.process("machine learning")
    result2 = await user_node.process("climate change")
    result3 = await append_node.process("renewable energy")

    # Reset conversation if needed
    await system_node.reset_conversation()


if __name__ == "__main__":
    asyncio.run(main())

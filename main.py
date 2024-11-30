from dotenv import load_dotenv
import os
import asyncio
from chainable_llm import (
    LLMNode,
    LLMConfig,
    PromptConfig,
    InputType,
    StreamConfig,
    TextNormalizer,
)


async def main():
    load_dotenv()

    # Buat node LLM
    node = LLMNode(
        llm_config=LLMConfig(
            provider="anthropic",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model="claude-3-sonnet-20240229",
            streaming=StreamConfig(enabled=True, chunk_size=10),
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="You are a helpful assistant.",
            template="Answer this question: {input}",
        ),
        transformer=TextNormalizer(),
    )

    # Proses input
    response = await node.process("What is artificial intelligence?")
    print(response.content)


if __name__ == "__main__":
    asyncio.run(main())

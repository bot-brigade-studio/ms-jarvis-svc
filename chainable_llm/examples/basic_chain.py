# chainable_llm/examples/basic_chain.py
import asyncio
import os
from dotenv import load_dotenv
from ..core.types import (
    LLMConfig, 
    PromptConfig, 
    InputType
)
from ..nodes.base import LLMNode
from ..transformers.implementations import TextNormalizer

async def main():
    # Load environment variables
    load_dotenv()

    # Validate API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if not openai_key or not anthropic_key:
        raise ValueError("Missing API keys in environment variables")

    try:
        # Create a summarization node
        summarizer = LLMNode(
            llm_config=LLMConfig(
                provider="anthropic",
                api_key=anthropic_key,
                model="claude-3-5-sonnet-20240620",
                temperature=0.3,
                max_tokens=1000  # Specify reasonable max_tokens
            ),
            prompt_config=PromptConfig(
                input_type=InputType.USER_PROMPT,
                base_system_prompt="You are a precise summarizer.",
                template="Summarize this text in 2-3 sentences: {input}"
            ),
            transformer=TextNormalizer()
        )

        # Create an analysis node
        analyzer = LLMNode(
            llm_config=LLMConfig(
                provider="openai",
                api_key=openai_key,
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=1000  # Specify reasonable max_tokens
            ),
            prompt_config=PromptConfig(
                input_type=InputType.USER_PROMPT,
                base_system_prompt="You are an insightful analyst.",
                template="Analyze the key points in this text: {input}"
            ),
            next_node=summarizer
        )

        # Test input
        test_input = """
        Artificial Intelligence has transformed various industries in recent years.
        Machine learning algorithms are becoming increasingly sophisticated, enabling
        applications from autonomous vehicles to medical diagnosis. The impact on
        society has been profound, raising both opportunities and ethical concerns.
        """

        # Process the chain
        result = await analyzer.process(test_input)

        # Print results
        print("\nInput Text:")
        print(test_input)
        print("\nFinal Result:")
        print(result.content)

        # if result.error:
        #     print("\nError occurred:", result.error)

        # # Print conversation histories
        # print("\nAnalyzer Conversation:")
        # for msg in analyzer.conversation.messages:
        #     print(f"{msg.role.value}: {msg.content}")

        # print("\nSummarizer Conversation:")
        # for msg in summarizer.conversation.messages:
        #     print(f"{msg.role.value}: {msg.content}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
# examples/smart_streaming.py

# how to start:
# python -m examples.smart_streaming

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from dotenv import load_dotenv
from typing import Optional, Dict
from core.types import (
    LLMConfig, 
    PromptConfig, 
    InputType,
    StreamConfig,
    StreamChunk,
    NodeContext,
    RouteDecision
)
from nodes.base import LLMNode

async def stream_callback(chunk: StreamChunk):
    """Simple callback to print streaming chunks"""
    print(f"{chunk.content}", end="", flush=True)
    if chunk.done:
        print("\n--- Stream completed ---\n")

async def fingerprint_router(content: str, context: NodeContext) -> RouteDecision:
    """
    Route based on content fingerprint from structured JSON response
    """
    try:

        # print(f"Fingerprint router received: {content}")
        print("\n\n\n")
        # print(f"Fingerprint router context: {context}")
        
        # Parse the JSON response from the fingerprint node
        analysis = json.loads(content)
        
        route_type = analysis.get("route_type")
        complexity = analysis.get("complexity_score", 0)
        requires_breakdown = analysis.get("requires_breakdown", False)
        
        if complexity >= 7 or requires_breakdown:
            return RouteDecision(
                route_id="small_model",
                user_input_transform=context.original_input,
                system_prompt_additions=analysis.get("breakdown_guidance", "Break down complex concepts into simpler terms.")
            )
        elif complexity >= 4:
            return RouteDecision(
                route_id="small_model",
                user_input_transform=f"Explain in simpler terms: {context.original_input}",
                system_prompt_additions=analysis.get("simplification_guidance", "Focus on clarity and simplicity.")
            )
        else:
            return RouteDecision(
                route_id="final_response",
                user_input_transform=context.original_input
            )
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        return RouteDecision(
            route_id="final_response",
            user_input_transform=context.original_input
        )

async def create_streaming_flow():
    """Create the streaming flow with multiple nodes"""
    openai_api_key = os.getenv("OPENAI_API_KEY")
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not openai_api_key or not anthropic_api_key:
        raise ValueError("API keys not found in environment variables")

    # Create the final response node
    final_response = LLMNode(
        name="final_response",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-3.5-turbo",
            temperature=0.7,
            streaming=StreamConfig(
                enabled=True,
                chunk_size=10
            )
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            template="Provide a clear response to: {input}",
            base_system_prompt="You are a helpful assistant focused on clear communication."
        ),
        stream_callback=stream_callback
    )

    # Create the small model aggregator
    small_model = LLMNode(
        name="small_model",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-3.5-turbo",
            temperature=0.5,
            streaming=StreamConfig(
                enabled=True,
                chunk_size=10
            )
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            template="Simplify and explain: {input}",
            base_system_prompt="You are an expert at simplifying complex topics."
        ),
        stream_callback=stream_callback,
        next_node=final_response
    )

    # Create the main fingerprinting node with Claude
    fingerprint_node = LLMNode(
        name="fingerprint",
        llm_config=LLMConfig(
            provider="anthropic",
            api_key=anthropic_api_key,
            model="claude-3-sonnet-20240229",
            temperature=0.1,  # Lower temperature for more consistent analysis
            streaming=StreamConfig(
                enabled=True,
                chunk_size=10
            )
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="""
Provide your analysis in this exact JSON structure:
{
    "route_type": "direct|simplify|breakdown",
    "complexity_score": <1-10>,
    "requires_breakdown": <boolean>,
    "reasoning": "<brief explanation>",
    "breakdown_guidance": "<if complex, guidance for breakdown>",
    "simplification_guidance": "<if technical, guidance for simplification>"
}
Ensure the response is valid JSON. Complexity score guide:
1-3: Simple, direct questions
4-6: Moderate complexity, may need simplification
7-10: Complex topics requiring breakdown""",
             template="Analyze and route this query: {input}"
        ),
        stream_callback=stream_callback,
        routes={
            "small_model": small_model,
            "final_response": final_response
        }
    )
    
    fingerprint_node.router = fingerprint_router

    return fingerprint_node

async def main():
    # Load environment variables
    load_dotenv()

    # Create the flow
    flow = await create_streaming_flow()

    # Test cases with expected routing
    test_cases = [
        # "What is the weather like today?",  # Simple (1-3)
        # "Explain how neural networks learn patterns in data",  # Moderate (4-6)
        "Explain quantum entanglement and its implications for quantum computing, including mathematical formulations",  # Complex (7-10)
        # "What's the relationship between consciousness and quantum mechanics in the context of free will?",  # Complex (7-10)
        # "How do I make a sandwich?",  # Simple (1-3)
    ]

    for test_input in test_cases:
        print(f"\n=== Processing: {test_input} ===\n")
        async for chunk in flow.process_stream(test_input):
            pass
        print("\n=== Processing Complete ===\n")

if __name__ == "__main__":
    asyncio.run(main())
# chainable_llm/examples/smart_routing_flow.py

import os
import json
from dotenv import load_dotenv
from chainable_llm.core.types import InputType, LLMConfig, NodeContext, PromptConfig, RouteDecision
from chainable_llm.nodes.enhanced_base import EnhancedLLMNode
from chainable_llm.transformers.base import DataTransformer

async def create_smart_flow():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    # Create specialized nodes first
    creative_node = EnhancedLLMNode(
        name="creative",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.9
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            template="Create creative content for: {input}",
            base_system_prompt="You are a creative writer focused on engaging content."
        )
    )

    analytical_node = EnhancedLLMNode(
        name="analytical",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.3
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            template="Perform detailed analysis of: {input}",
            base_system_prompt="You are an analytical expert focused on deep insights."
        )
    )

    factual_node = EnhancedLLMNode(
        name="factual",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-3.5-turbo",
            temperature=0.1
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            template="Verify and provide factual information about: {input}",
            base_system_prompt="You are a fact checker focused on accuracy."
        ),
    )

    # Create routing node (initial node)
    routing_node = EnhancedLLMNode(
        name="router",
        llm_config=LLMConfig(
            provider="openai",
            api_key=openai_api_key,
            model="gpt-4",
            temperature=0.1
        ),
        prompt_config=PromptConfig(
            input_type=InputType.USER_PROMPT,
            base_system_prompt="""You are an intelligent router that analyzes queries and determines the best processing path.

            Your task is to:
            1. Analyze the input query
            2. Determine the most appropriate route
            3. Provide routing decision in JSON format

            Available routes:
            - to_creative: for creative tasks, storytelling, content generation
            - to_analytical: for analysis, insights, complex reasoning
            - to_factual: for fact checking, verification, objective information

            Output must be valid JSON with this format:
            {
                "route_id": "route_name",
                "reason": "explanation of choice",
                "priority": "high/medium/low",
                "guidance": "specific instructions for handling node"
            }
            """,
            template="Analyze and route this query: {input}"
        ),
        routes={
            "to_creative": creative_node,
            "to_analytical": analytical_node,
            "to_factual": factual_node
        }
    )

    async def parse_routing_response(content: str, context: NodeContext) -> RouteDecision:
        """Parse LLM response and convert to RouteDecision"""
        try:
            clean_content = content.strip()
            if clean_content.startswith("```json"):
                clean_content = clean_content.replace("```json", "").replace("```", "")
            
            decision = json.loads(clean_content)
            
            # Create system prompt addition from the guidance
            system_prompt_addition = f"Additional context: {decision.get('guidance', '')}"
            
            return RouteDecision(
                route_id=decision["route_id"],
                system_prompt_additions=system_prompt_addition,
                metadata={
                    "reason": decision["reason"],
                    "priority": decision["priority"],
                    "guidance": decision["guidance"]
                }
            )
        except Exception as e:
            print(f"Error in routing: {e}")
            return RouteDecision(route_id="to_factual")

    # Set the router function
    routing_node.router = parse_routing_response

    return routing_node

async def main():
    load_dotenv()
    flow = await create_smart_flow()
    
    # Test cases
    test_cases = [
        # "Write a story about a magical forest",
        # "Analyze the impact of AI on healthcare",
        "What are the key events of World War 2?",
        # "Create a marketing slogan for a new smartphone",
        # "Explain quantum computing principles",
        # "Verify these historical dates and events"
    ]
    
    for query in test_cases:
        print("\n" + "="*50)
        print(f"Processing query: {query}")
        
        try:
            # Process the query
            response = await flow.process(query)
            
            # Print routing decision
            if response.route_decision and response.route_decision.metadata:
                print("\nRouting Decision:")
                print(f"Route: {response.route_decision.route_id}")
                print(f"Reason: {response.route_decision.metadata.get('reason')}")
                print(f"Priority: {response.route_decision.metadata.get('priority')}")
                print(f"Guidance: {response.route_decision.metadata.get('guidance')}")
            
            # Print final response
            # print("\nFinal Response:")
            # print(response.content)
            
            # # Print conversation history
            # print("\nConversation Flow:")
            # for node in response.node_path:
            #     print(f"-> {node}")
            
        except Exception as e:
            print(f"Error processing query: {e}")
        
        # Reset conversations after each query
        await flow.reset_conversation()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
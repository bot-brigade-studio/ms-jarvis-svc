import asyncio
import os
from dotenv import load_dotenv
from playground.pipelines.chat import Pipeline

# Load environment variables
load_dotenv()

async def run_test_conversation():
    # Initialize Pipeline with API keys from environment variables
    pipeline = Pipeline(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    # Test cases
    test_queries = [
        "What is the capital of France?",  # Simple factual query (likely route 1)
        "Can you help me write a complex essay about the impact of AI on society?",  # Complex query (likely route 3)
        "I need help with my math homework: 2 + 2 = ?",  # Simple guided query (likely route 2)
    ]

    # Run test conversation
    conversation_id = "test_conversation"
    
    for query in test_queries:
        print("\n" + "="*50)
        print(f"User Query: {query}")
        
        try:
            response, route_info = await pipeline.process_query(
                query=query,
                conversation_id=conversation_id
            )
            
            print(f"\nRoute Info: {route_info}")
            print(f"\nAssistant Response: {response}")
            
        except Exception as e:
            print(f"Error processing query: {str(e)}")

    # Test context retention
    follow_up_query = "What was my previous question?"
    print("\n" + "="*50)
    print(f"Follow-up Query: {follow_up_query}")
    
    try:
        response, route_info = await pipeline.process_query(
            query=follow_up_query,
            conversation_id=conversation_id
        )
        
        print(f"\nRoute Info: {route_info}")
        print(f"\nAssistant Response: {response}")
        
    except Exception as e:
        print(f"Error processing follow-up query: {str(e)}")

def main():
    # Run the async test
    asyncio.run(run_test_conversation())

if __name__ == "__main__":
    main()
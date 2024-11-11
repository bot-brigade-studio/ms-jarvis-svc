import asyncio
import os
import logging
from dotenv import load_dotenv
from playground.pipelines.chat_stream import Pipeline

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_test_conversation():
    logger.info("Starting test conversation")
    
    pipeline = Pipeline(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )

    test_queries = [
        # "What is the capital of France?",
        # "Can you help me write a complex essay about the impact of AI on society?",
        # "I need help with my math homework: 2 + 2 = ?",
        "I have 5 people and 3 cars. Each car can take 2 people. What's the minimum trips needed to transport everyone?"
    ]

    conversation_id = "test_conversation"
    
    for query in test_queries:
        logger.info("="*50)
        logger.info(f"Testing query: {query}")
        
        try:
            full_response, route_info = await pipeline.process_query(
                query=query,
                conversation_id=conversation_id
            )
            
            logger.info(f"Route Info: {route_info}")
            logger.info(f"Response: {full_response}")
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)

def main():
    asyncio.run(run_test_conversation())

if __name__ == "__main__":
    main()
from typing import Tuple, Dict, Optional
import json
import logging
import asyncio

from playground.module.llm_service import LLMService
from playground.module.memory import MemoryStore
from playground.prompts.system_prompts import SystemPrompts
from playground.prompts.user_prompts import UserPrompts

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Pipeline:
    def __init__(self, anthropic_api_key: str, openai_api_key: str):
        self.llm_service = LLMService(anthropic_api_key, openai_api_key)
        self.memory = MemoryStore()
        self.system_prompts = SystemPrompts()
        self.user_prompts = UserPrompts()

    async def process_query(
        self,
        query: str,
        conversation_id: str = "default"
    ) -> Tuple[str, Dict]:
        logger.info(f"Processing query: {query}")
        logger.info(f"Conversation ID: {conversation_id}")

        # Get context
        context = self.memory.get_context(conversation_id)
        logger.info(f"Retrieved context: {context}")

        # Get fingerprint
        logger.info("Getting query fingerprint...")
        fingerprint_response = await self._get_fingerprint_stream(query, context)
        logger.info(f"Fingerprint response: {fingerprint_response}")

        route_info = self._parse_fingerprint(fingerprint_response)
        logger.info(f"Route info: {route_info}")

        # Process based on route
        logger.info(f"Processing route {route_info['route']}...")
        response = await self._process_route_stream(
            query=query,
            route_info=route_info,
            context=context
        )

        # Save to memory
        logger.info("Saving interaction to memory...")
        self.memory.add_interaction(
            conversation_id=conversation_id,
            role="user",
            content=query,
            route_info=route_info
        )
        
        self.memory.add_interaction(
            conversation_id=conversation_id,
            role="assistant",
            content=response,
            route_info=route_info
        )

        return response, route_info

    async def _get_fingerprint_stream(self, query: str, context: Optional[str] = None) -> str:
        """Get query fingerprint using stream"""
        logger.info("Starting fingerprint stream...")
        full_response = ""
        
        async for chunk in self.llm_service.generate_stream(
            model_name="claude-3-sonnet-20240229",
            messages=[{
                "role": "user",
                "content": query,
            }],
            system_prompt=self.system_prompts.FINGERPRINT
        ):
            if chunk.content:
                full_response += chunk.content
            
            if chunk.is_final:
                break

        return full_response

    async def _process_route_stream(
        self,
        query: str,
        route_info: Dict,
        context: Optional[str] = None
    ) -> str:
        """Process query based on route using stream"""
        route = route_info["route"]
        full_response = ""
        
        if route == 1:  # DIRECT_SMALL
            logger.info("Processing DIRECT_SMALL route")
            model = "gpt-4o-mini"
            messages = [{
                "role": "user",
                "content": self.user_prompts.route_1(query, context)
            }]
            system_prompt = self.system_prompts.ROUTE_1

        elif route == 2:  # GUIDED_SMALL
            logger.info("Processing GUIDED_SMALL route")
            model = "gpt-4o-mini"
            messages = [{
                "role": "user",
                "content": self.user_prompts.route_2(
                    query,
                    route_info["guidance"],
                    context
                )
            }]
            system_prompt = self.system_prompts.ROUTE_2

        else:  # DIRECT_LARGE
            logger.info("Processing DIRECT_LARGE route")
            model = "claude-3-sonnet-20240229"
            messages = [{
                "role": "user",
                "content": self.user_prompts.route_3(query, context)
            }]
            system_prompt = self.system_prompts.ROUTE_3

        async for chunk in self.llm_service.generate_stream(
            model_name=model,
            messages=messages,
            system_prompt=system_prompt
        ):
            if chunk.content:
                full_response += chunk.content
                logger.debug(f"Response chunk received: {chunk.content}")
                
            if chunk.is_final:
                logger.info("Response stream completed")
                break

        return full_response

    def _parse_fingerprint(self, response: str) -> Dict:
        """Parse fingerprint response"""
        try:
            logger.info("Parsing fingerprint response")
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse fingerprint: {e}")
            raise ValueError("Invalid fingerprint response format")
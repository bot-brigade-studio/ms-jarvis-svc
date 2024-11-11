from typing import List, Tuple, Dict, Optional
import json
import logging

from playground.module.llm_service import LLMService
from playground.module.memory import MemoryStore
from playground.prompts.system_prompts import SystemPrompts
from playground.prompts.user_prompts import UserPrompts
import re

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
        # First add the new interaction
        self.memory.add_interaction(
            conversation_id=conversation_id,
            role="user",
            content=query,
            route_info={}
        )

        # Then get context and format messages
        context = self.memory.get_context(conversation_id)
        logger.info(f"Retrieved context {conversation_id} -> : {context}")
        messages = self.memory.format_to_messages(context)

        if not messages:
            raise ValueError("No messages found in context")

        full_response = ""
        json_string = ""
        current_route = 0
        async for chunk in self.llm_service.generate_stream(
            model_name="claude-3-5-sonnet-20241022",
                messages=messages,
            system_prompt=self.system_prompts.FINGERPRINT
        ):
            if chunk.content:
                json_string += chunk.content
                route_match = re.search(r'"route":\s*([123])', json_string)
                if route_match:
                    current_route = int(route_match.group(1))
                    if current_route == 1:
                        break
                
            if chunk.is_final:
                break

        json_dict = self._parse_json_string(json_string)
        if current_route == 1:
            logger.info("Processing DIRECT_SMALL route")
            async for chunk in self.llm_service.generate_stream(
                model_name="gpt-4o-mini",
                messages=messages,
                system_prompt=self.system_prompts.ROUTE_1
            ):
                if chunk.content:
                    full_response += chunk.content
                    logger.debug(f"Response chunk received: {chunk.content}")
                
                if chunk.is_final:
                    logger.info("Response stream completed")
                    break
            
        elif current_route == 2:
            logger.info("Processing GUIDED_SMALL route")
            guidance = json_dict["guidance"]
            self.system_prompts.set_guidance(guidance)
            system_prompt = self.system_prompts.ROUTE_2

            async for chunk in self.llm_service.generate_stream(
                model_name="gpt-4o-mini",
                messages=messages,
                system_prompt=system_prompt
            ):
                if chunk.content:
                    full_response += chunk.content
                    logger.debug(f"Response chunk received: {chunk.content}")
                
                if chunk.is_final:
                    logger.info("Response stream completed")
                    break

        elif current_route == 3:
            logger.info("Processing DIRECT_LARGE route")
            response = json_dict["response"]
            full_response = response

            

        return full_response, current_route

    def _parse_json_string(self, json_string: str) -> Dict:
        """Parse json string"""
        try:
            logger.info("Parsing json string")
            logger.info(f"JSON String: {json_string}")
            return json.loads(json_string)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse json string: {e}")
            raise ValueError("Invalid fingerprint response format")
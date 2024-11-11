# playground/pipelines/chat.py
from typing import Tuple, Dict, Optional
import json

from playground.module.llm_service import LLMService
from playground.module.memory import MemoryStore
from playground.prompts.system_prompts import SystemPrompts
from playground.prompts.user_prompts import UserPrompts

class Pipeline:
    def __init__(self, anthropic_api_key: str, openai_api_key: str):
        self.llm_service = LLMService(anthropic_api_key, openai_api_key)
        self.memory = MemoryStore()
        self.system_prompts = SystemPrompts()
        self.user_prompts = UserPrompts()

    async def process_query(
        self,
        query: str,
        conversation_id: str = "default"  # Use default conversation for POC
    ) -> Tuple[str, Dict]:
        # Get context
        context = self.memory.get_context(conversation_id)

        # Get fingerprint
        fingerprint_response = await self._get_fingerprint(query, context)
        route_info = self._parse_fingerprint(fingerprint_response)

        # Process based on route
        response = await self._process_route(
            query=query,
            route_info=route_info,
            context=context
        )

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

    async def _get_fingerprint(self, query: str, context: Optional[str] = None) -> str:
        """Get query fingerprint from Anthropic"""
        return await self.llm_service.generate_response(
            model_name="claude-3-sonnet-20240229",
            messages=[{
                "role": "user",
                "content": self.user_prompts.fingerprint(query, context)
            }],
            system_prompt=self.system_prompts.FINGERPRINT
        )

    async def _process_route(
        self,
        query: str,
        route_info: Dict,
        context: Optional[str] = None
    ) -> str:
        """Process query based on route"""
        route = route_info["route"]

        if route == 1:  # DIRECT_SMALL
            return await self.llm_service.generate_response(
                model_name="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": self.user_prompts.route_1(query, context)
                }],
                system_prompt=self.system_prompts.ROUTE_1
            )

        elif route == 2:  # GUIDED_SMALL
            return await self.llm_service.generate_response(
                model_name="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": self.user_prompts.route_2(
                        query,
                        route_info["guidance"],
                        context
                    )
                }],
                system_prompt=self.system_prompts.ROUTE_2
            )

        else:  # DIRECT_LARGE
            return await self.llm_service.generate_response(
                model_name="claude-3-sonnet-20240229",
                messages=[{
                    "role": "user",
                    "content": self.user_prompts.route_3(query, context)
                }],
                system_prompt=self.system_prompts.ROUTE_3
            )

    def _parse_fingerprint(self, response: str) -> Dict:
        """Parse fingerprint response"""
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("Invalid fingerprint response format")

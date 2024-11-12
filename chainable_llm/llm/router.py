# llm/router.py
from typing import Optional, List
from enum import Enum
from .base import BaseLLMProvider
from ..core.types import LLMResponse
from ..core.logging import logger

class RouteType(Enum):
    DIRECT_QUERY = 1
    GUIDED_QUERY = 2
    COMPLEX_QUERY = 3
    
class QueryClassifier:
    """Classifies incoming queries to determine routing"""
    async def classify(self, query: str) -> RouteType:
        # Implementation would use actual classification logic
        # For testing, we'll use simple keyword matching
        if "guide" in query.lower():
            return RouteType.GUIDED_QUERY
        elif "complex" in query.lower():
            return RouteType.COMPLEX_QUERY
        return RouteType.DIRECT_QUERY

class LLMRouter:
    def __init__(
        self,
        large_model: BaseLLMProvider,
        small_model: BaseLLMProvider,
        classifier: QueryClassifier
    ):
        self.large_model = large_model
        self.small_model = small_model
        self.classifier = classifier

    async def process_query(
        self,
        query: str,
        conversation_history: Optional[List[str]] = None
    ) -> LLMResponse:
        try:
            # Classify query
            route_type = await self.classifier.classify(query)
            
            # Build context
            context = self._build_context(conversation_history)
            
            # Construct prompt
            prompt = self._construct_prompt(query, route_type, context)
            
            # Route to appropriate model
            if route_type in [RouteType.DIRECT_QUERY, RouteType.GUIDED_QUERY]:
                response = await self.small_model.generate(prompt, context)
            else:
                response = await self.large_model.generate(prompt, context)
                
            return LLMResponse(
                content=response["content"],
                route_type=route_type,
                final_prompt=prompt,
                context=context
            )
            
        except Exception as e:
            logger.error(f"Router error: {str(e)}")
            raise

    def _build_context(self, conversation_history: Optional[List[str]]) -> dict:
        if not conversation_history:
            return {}
        return {"history": conversation_history}

    def _construct_prompt(
        self,
        query: str,
        route_type: RouteType,
        context: dict
    ) -> str:
        # Implement prompt construction logic based on route type
        prompts = {
            RouteType.DIRECT_QUERY: "Answer the following question",
            RouteType.GUIDED_QUERY: "Provide step-by-step guidance",
            RouteType.COMPLEX_QUERY: "Perform detailed analysis"
        }
        
        base_prompt = prompts[route_type]
        return f"{base_prompt}: {query}"
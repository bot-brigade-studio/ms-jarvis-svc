# tests/test_llm_routing.py
# how to run : pytest chainable_llm/tests/test_llm_routing.py
import pytest
from typing import Optional, List
from unittest.mock import AsyncMock, patch
from enum import Enum

from chainable_llm.llm.router import LLMRouter

class RouteType(Enum):
    DIRECT_QUERY = 1          # Direct to small model
    GUIDED_QUERY = 2          # To small model with guidance
    COMPLEX_QUERY = 3         # Direct to large model

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

class RoutingTestCase:
    def __init__(
        self,
        input_query: str,
        expected_route: RouteType,
        expected_model: str,
        expected_prompt: Optional[str] = None,
        conversation_history: Optional[List[str]] = None
    ):
        self.input_query = input_query
        self.expected_route = expected_route
        self.expected_model = expected_model
        self.expected_prompt = expected_prompt
        self.conversation_history = conversation_history or []

@pytest.mark.asyncio
class TestLLMRouting:
    @pytest.fixture
    async def setup_mocks(self):
        """Setup common mocks for testing"""
        with patch('your_module.OpenAIProvider') as mock_large_model, \
             patch('your_module.ClaudeProvider') as mock_small_model:
            
            # Configure mock responses
            mock_large_model.generate.return_value = AsyncMock(
                return_value={"content": "Large model response"}
            )
            mock_small_model.generate.return_value = AsyncMock(
                return_value={"content": "Small model response"}
            )
            
            yield {
                "large_model": mock_large_model,
                "small_model": mock_small_model
            }

    @pytest.mark.parametrize("test_case", [
        # Route 1: Direct queries to small model
        RoutingTestCase(
            input_query="What is the weather today?",
            expected_route=RouteType.DIRECT_QUERY,
            expected_model="gpt-3.5-turbo",
            expected_prompt="What is the weather today?"
        ),
        
        # Route 2: Guided queries to small model
        RoutingTestCase(
            input_query="Please guide me through machine learning concepts",
            expected_route=RouteType.GUIDED_QUERY,
            expected_model="gpt-3.5-turbo",
            expected_prompt="I'll guide you through machine learning concepts. "
                          "Let's break this down step by step."
        ),
        
        # Route 3: Complex queries to large model
        RoutingTestCase(
            input_query="Give me a complex analysis of quantum computing",
            expected_route=RouteType.COMPLEX_QUERY,
            expected_model="gpt-4",
            expected_prompt="Provide a detailed analysis of quantum computing"
        ),
        
        # Test with conversation history
        RoutingTestCase(
            input_query="Continue our discussion",
            expected_route=RouteType.DIRECT_QUERY,
            expected_model="gpt-3.5-turbo",
            expected_prompt="Continue our discussion",
            conversation_history=["Previous message 1", "Previous message 2"]
        ),
    ])
    async def test_routing_logic(self, setup_mocks, test_case):
        """Test the routing logic for different query types"""
        mocks = setup_mocks
        
        # Create router instance
        router = LLMRouter(
            large_model=mocks["large_model"],
            small_model=mocks["small_model"],
            classifier=QueryClassifier()
        )
        
        # Process query
        result = await router.process_query(
            query=test_case.input_query,
            conversation_history=test_case.conversation_history
        )
        
        # Verify routing
        assert result.route_type == test_case.expected_route
        
        # Verify model selection
        if test_case.expected_route in [RouteType.DIRECT_QUERY, RouteType.GUIDED_QUERY]:
            mocks["small_model"].generate.assert_called_once()
            mocks["large_model"].generate.assert_not_called()
        else:
            mocks["large_model"].generate.assert_called_once()
            mocks["small_model"].generate.assert_not_called()
        
        # Verify prompt construction
        if test_case.expected_prompt:
            assert test_case.expected_prompt in result.final_prompt
        
        # Verify conversation history handling
        if test_case.conversation_history:
            assert all(
                msg in result.context 
                for msg in test_case.conversation_history
            )

    @pytest.mark.parametrize("error_scenario", [
        "classification_error",
        "model_error",
        "routing_error"
    ])
    async def test_error_handling(self, setup_mocks, error_scenario):
        """Test error handling for different failure scenarios"""
        mocks = setup_mocks
        
        if error_scenario == "classification_error":
            classifier = AsyncMock()
            classifier.classify.side_effect = Exception("Classification failed")
        else:
            classifier = QueryClassifier()
            
        router = LLMRouter(
            large_model=mocks["large_model"],
            small_model=mocks["small_model"],
            classifier=classifier
        )
        
        if error_scenario == "model_error":
            mocks["small_model"].generate.side_effect = Exception("Model error")
        elif error_scenario == "routing_error":
            router.route = AsyncMock(side_effect=Exception("Routing error"))
            
        # Test error handling
        with pytest.raises(Exception) as exc_info:
            await router.process_query("Test query")
            
        assert str(exc_info.value) in [
            "Classification failed",
            "Model error",
            "Routing error"
        ]

    async def test_conversation_context(self, setup_mocks):
        """Test conversation history handling"""
        mocks = setup_mocks
        router = LLMRouter(
            large_model=mocks["large_model"],
            small_model=mocks["small_model"],
            classifier=QueryClassifier()
        )
        
        # Simulate conversation flow
        conversation = [
            "User: Initial question",
            "Assistant: Initial response",
            "User: Follow-up question"
        ]
        
        result = await router.process_query(
            query="Continue the conversation",
            conversation_history=conversation
        )
        
        # Verify conversation context is maintained
        assert all(msg in result.context for msg in conversation)
        assert result.context_length == len(conversation)

    async def test_prompt_construction(self, setup_mocks):
        """Test prompt construction for different routes"""
        mocks = setup_mocks
        router = LLMRouter(
            large_model=mocks["large_model"],
            small_model=mocks["small_model"],
            classifier=QueryClassifier()
        )
        
        test_cases = [
            {
                "query": "Simple question",
                "expected_prefix": "Answer the following question",
                "expected_route": RouteType.DIRECT_QUERY
            },
            {
                "query": "Guide me through",
                "expected_prefix": "Provide step-by-step guidance",
                "expected_route": RouteType.GUIDED_QUERY
            },
            {
                "query": "Complex analysis needed",
                "expected_prefix": "Perform detailed analysis",
                "expected_route": RouteType.COMPLEX_QUERY
            }
        ]
        
        for case in test_cases:
            result = await router.process_query(case["query"])
            assert case["expected_prefix"] in result.final_prompt
            assert result.route_type == case["expected_route"]
# chainable_llm/tests/test_nodes.py

import pytest
from unittest.mock import AsyncMock, patch
from chainable_llm.core.types import LLMConfig, PromptConfig, InputType, LLMResponse
from chainable_llm.nodes.base import LLMNode
from chainable_llm.transformers.implementations import TextNormalizer

@pytest.mark.asyncio
async def test_basic_node_processing():
    config = LLMConfig(
        provider="openai",
        api_key="test-key",
        model="gpt-4"
    )
    
    prompt_config = PromptConfig(
        input_type=InputType.USER_PROMPT,
        template="Process: {input}",
        base_system_prompt="Test system"
    )

    with patch('chainable_llm.llm.factory.LLMFactory.create') as mock_create:
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = LLMResponse(
            content="Processed result",
            metadata={}
        )
        mock_create.return_value = mock_llm

        node = LLMNode(
            llm_config=config,
            prompt_config=prompt_config,
            transformer=TextNormalizer()
        )

        result = await node.process("test input")
        assert result.content == "Processed result"
        mock_llm.generate.assert_called_once()
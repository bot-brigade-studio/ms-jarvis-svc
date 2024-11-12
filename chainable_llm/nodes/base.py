# nodes/base.py
from typing import Optional, Callable, Any

from chainable_llm.transformers.base import DataTransformer
from ..core.types import (
    LLMConfig, 
    PromptConfig, 
    LLMResponse, 
    ConversationHistory,
    MessageRole
)
from ..llm.factory import LLMFactory
from ..core.logging import logger

class LLMNode:
    def __init__(
        self,
        llm_config: LLMConfig,
        prompt_config: PromptConfig,
        transformer: Optional[DataTransformer] = None,
        next_node: Optional['LLMNode'] = None,
        condition: Optional[Callable[[str], bool]] = None
    ):
        self.llm = LLMFactory.create(llm_config)
        self.prompt_config = prompt_config
        self.transformer = transformer
        self.next_node = next_node
        self.condition = condition
        self.conversation = ConversationHistory()

    async def process(self, input_data: Any) -> LLMResponse:
        try:
            # Transform input if transformer exists
            if self.transformer:
                input_text = await self.transformer.transform(input_data)
            else:
                input_text = str(input_data)

            # Add user input to conversation
            self.conversation.add_message(
                role=MessageRole.USER,
                content=input_text
            )

            # Generate LLM response
            response = await self.llm.generate(
                system_prompt=self.prompt_config.base_system_prompt,
                conversation=self.conversation,
                temperature=self.llm.config.temperature,
                max_tokens=self.llm.config.max_tokens
            )

            # Add assistant response to conversation
            self.conversation.add_message(
                role=MessageRole.ASSISTANT,
                content=response.content
            )

            # Process next node if conditions are met
            if self.next_node and (not self.condition or self.condition(response.content)):
                return await self.next_node.process(response.content)

            return response

        except Exception as e:
            logger.error("node_processing_error", error=str(e))
            return LLMResponse(
                content="",
                metadata={},
                error=str(e)
            )
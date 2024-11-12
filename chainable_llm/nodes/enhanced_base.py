# nodes/enhanced_base.py
from typing import Optional, Callable, Any, Dict

from chainable_llm.transformers.base import DataTransformer
from ..core.types import (
    LLMConfig,
    NodeContext, 
    PromptConfig, 
    LLMResponse, 
    ConversationHistory,
    MessageRole,
    InputType,
    RouteDecision
)
from ..llm.factory import LLMFactory
from ..core.logging import logger

# nodes/enhanced_base.py
class EnhancedLLMNode:
    def __init__(
        self,
        name: str,
        llm_config: LLMConfig,
        prompt_config: PromptConfig,
        transformer: Optional[DataTransformer] = None,
        router: Optional[Callable[[str, NodeContext], RouteDecision]] = None,
        routes: Optional[Dict[str, 'EnhancedLLMNode']] = None
    ):
        self.name = name
        self.llm = LLMFactory.create(llm_config)
        self.prompt_config = prompt_config
        self.transformer = transformer
        self.router = router
        self.routes = routes or {}
        self.conversation = ConversationHistory()

    async def _build_prompt(self, context: NodeContext) -> tuple[Optional[str], str]:
        """
        Build the final prompt based on the prompt configuration and context.
        """
        # Format the template with the current input
        formatted_input = self.prompt_config.template.format(input=context.current_input)
        
        if self.prompt_config.input_type == InputType.SYSTEM_PROMPT:
            system_prompt = formatted_input
        elif self.prompt_config.input_type == InputType.APPEND_SYSTEM:
            base_system = self.prompt_config.base_system_prompt or ""
            system_prompt = f"{base_system}\n{formatted_input}"
        else:  # InputType.USER_PROMPT
            system_prompt = self.prompt_config.base_system_prompt or ""
            
        # Add any accumulated system prompt additions from routing
        if context.system_prompt_additions:
            system_prompt = f"{system_prompt}\n{' '.join(context.system_prompt_additions)}"
            
        return system_prompt, formatted_input if self.prompt_config.input_type == InputType.USER_PROMPT else ""

    async def reset_conversation(self):
        self.conversation = ConversationHistory()

    async def process(self, input_data: Any, context: Optional[NodeContext] = None) -> LLMResponse:
        try:
            # Initialize or update context
            if context is None:
                context = NodeContext(
                    original_input=str(input_data),
                    current_input=str(input_data)
                )
            
            # Transform input if transformer exists
            if self.transformer:
                transformed_input = await self.transformer.transform(context.current_input)
                context.current_input = transformed_input

            # Build prompts using template and context
            system_prompt, user_prompt = await self._build_prompt(context)

            # If we have a user prompt, add it to conversation
            if user_prompt:
                self.conversation.add_message(
                    role=MessageRole.USER,
                    content=user_prompt
                )
            
            # Generate LLM response
            response = await self.llm.generate(
                system_prompt=system_prompt,
                conversation=self.conversation,
                temperature=self.llm.config.temperature,
                max_tokens=self.llm.config.max_tokens
            )

            # Add assistant response to conversation
            self.conversation.add_message(
                role=MessageRole.ASSISTANT,
                content=response.content
            )

            # Determine routing if router exists
            route_decision = None
            if self.router:
                route_decision = await self.router(response.content, context)
                
                # If we have a valid route, update context and process next node
                if route_decision and route_decision.route_id in self.routes:
                    next_node = self.routes[route_decision.route_id]
                    
                    # Update context for next node
                    if route_decision.system_prompt_additions:
                        context.system_prompt_additions.append(route_decision.system_prompt_additions)
                    
                    # Either use transformed input or original input
                    context.current_input = (
                        route_decision.user_input_transform or context.original_input
                    )
                    
                    # Update metadata
                    context.metadata.update(route_decision.metadata)
                    
                    return await next_node.process(context.current_input, context)

            return LLMResponse(
                content=response.content,
                metadata={
                    **response.metadata,
                    "context": context.dict() if context else None
                },
                route_decision=route_decision
            )

        except Exception as e:
            logger.error(
                "node_processing_error", 
                error=str(e), 
                node_id=id(self),
                input_length=len(str(input_data))
            )
            return LLMResponse(
                content="",
                metadata={
                    "error_type": type(e).__name__,
                    "node_id": id(self)
                },
                error=str(e)
            )
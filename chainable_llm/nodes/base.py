from typing import AsyncIterator, Awaitable, Optional, Callable, Any, Dict

from core.streaming import StreamBuffer
from transformers.base import DataTransformer
from core.types import (
    LLMConfig,
    NodeContext,
    PromptConfig,
    LLMResponse,
    ConversationHistory,
    MessageRole,
    InputType,
    RouteDecision,
    StreamChunk,
)
from llm.factory import LLMFactory
from core.logging import logger


class LLMNode:
    def __init__(
        self,
        llm_config: LLMConfig,
        prompt_config: PromptConfig,
        name: str = None,
        transformer: Optional[DataTransformer] = None,
        next_node: Optional["LLMNode"] = None,
        condition: Optional[Callable[[str], bool]] = None,
        router: Optional[Callable[[str, NodeContext], RouteDecision]] = None,
        routes: Optional[Dict[str, "LLMNode"]] = None,
        stream_callback: Optional[Callable[[StreamChunk], Awaitable[None]]] = None,
    ):
        self.name = name
        self.llm = LLMFactory.create(llm_config)
        self.prompt_config = prompt_config
        self.transformer = transformer
        self.next_node = next_node
        self.condition = condition
        self.router = router
        self.routes = routes or {}
        self.conversation = ConversationHistory()
        self.stream_callback = stream_callback

    async def _build_prompt(
        self, context: NodeContext | str
    ) -> tuple[Optional[str], str]:
        """
        Build the final prompt based on the prompt configuration and context.
        Supports both string input (legacy) and NodeContext (enhanced).
        """
        input_text = (
            context.current_input if isinstance(context, NodeContext) else context
        )
        formatted_input = self.prompt_config.template.format(input=input_text)

        if self.prompt_config.input_type == InputType.SYSTEM_PROMPT:
            system_prompt = formatted_input
        elif self.prompt_config.input_type == InputType.APPEND_SYSTEM:
            base_system = self.prompt_config.base_system_prompt or ""
            system_prompt = f"{base_system}\n{formatted_input}"
        else:  # InputType.USER_PROMPT
            system_prompt = self.prompt_config.base_system_prompt or ""

        # Add system prompt additions if using enhanced context
        if isinstance(context, NodeContext) and context.system_prompt_additions:
            system_prompt = (
                f"{system_prompt}\n{' '.join(context.system_prompt_additions)}"
            )

        return system_prompt, (
            formatted_input
            if self.prompt_config.input_type == InputType.USER_PROMPT
            else ""
        )

    async def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation = ConversationHistory()

    async def process(
        self, input_data: Any, context: Optional[NodeContext] = None
    ) -> LLMResponse:
        """
        Process input through the LLM node with support for both legacy and enhanced routing.
        """
        try:
            # Handle context initialization
            if context is None and (self.router or self.routes):
                # Create context for enhanced routing
                context = NodeContext(
                    original_input=str(input_data), current_input=str(input_data)
                )

            # Transform input
            if self.transformer:
                transformed_input = await self.transformer.transform(
                    context.current_input if context else input_data
                )
                if context:
                    context.current_input = transformed_input
                else:
                    input_data = transformed_input

            # Build prompts
            system_prompt, user_prompt = await self._build_prompt(
                context if context else input_data
            )

            # Add user message to conversation if present
            if user_prompt:
                self.conversation.add_message(
                    role=MessageRole.USER, content=user_prompt
                )

            # Generate LLM response
            response = await self.llm.generate(
                system_prompt=system_prompt,
                conversation=self.conversation,
                temperature=self.llm.config.temperature,
                max_tokens=self.llm.config.max_tokens,
            )

            # Add assistant response to conversation
            self.conversation.add_message(
                role=MessageRole.ASSISTANT, content=response.content
            )

            # Enhanced routing
            if self.router and context:
                route_decision = await self.router(response.content, context)

                if route_decision and route_decision.route_id in self.routes:
                    next_node = self.routes[route_decision.route_id]

                    # Update context for next node
                    if route_decision.system_prompt_additions:
                        context.system_prompt_additions.append(
                            route_decision.system_prompt_additions
                        )

                    # Update input and metadata
                    context.current_input = (
                        route_decision.user_input_transform or context.original_input
                    )
                    context.metadata.update(route_decision.metadata)

                    # Process next node with updated context
                    return await next_node.process(context.current_input, context)

                # Include routing decision in response
                response.route_decision = route_decision

            # Legacy routing fallback
            elif self.next_node and (
                not self.condition or self.condition(response.content)
            ):
                return await self.next_node.process(response.content)

            # Add context to metadata if available
            if context:
                response.metadata["context"] = context.dict()

            return response

        except Exception as e:
            logger.error(
                "node_processing_error",
                error=str(e),
                node_id=id(self),
                input_length=len(str(input_data)),
            )
            return LLMResponse(
                content="",
                metadata={"error_type": type(e).__name__, "node_id": id(self)},
                error=str(e),
            )

    async def process_stream(
        self, input_data: Any, context: Optional[NodeContext] = None
    ) -> AsyncIterator[StreamChunk]:
        """Process input with streaming support."""
        try:
            # Initialize context if needed (similar to regular process)
            if context is None and (self.router or self.routes):
                context = NodeContext(
                    original_input=str(input_data), current_input=str(input_data)
                )

            # Transform input if needed
            if self.transformer:
                transformed_input = await self.transformer.transform(
                    context.current_input if context else input_data
                )
                if context:
                    context.current_input = transformed_input
                else:
                    input_data = transformed_input

            # Build prompts
            system_prompt, user_prompt = await self._build_prompt(
                context if context else input_data
            )

            # Add user message to conversation
            if user_prompt:
                self.conversation.add_message(
                    role=MessageRole.USER, content=user_prompt
                )

            # Generate streaming response
            buffer = StreamBuffer(self.llm.config.streaming)
            accumulated_content = []

            async for chunk in self.llm.generate_stream(
                system_prompt=system_prompt,
                conversation=self.conversation,
                temperature=self.llm.config.temperature,
                max_tokens=self.llm.config.max_tokens,
            ):
                accumulated_content.append(chunk.content)

                # Handle callback if configured
                if self.stream_callback:
                    await self.stream_callback(chunk)

                yield chunk

            # Add complete response to conversation history
            complete_content = "".join(accumulated_content)
            self.conversation.add_message(
                role=MessageRole.ASSISTANT, content=complete_content
            )

            # Handle routing if configured
            if self.router and context:
                route_decision = await self.router(complete_content, context)

                if route_decision and route_decision.route_id in self.routes:
                    next_node = self.routes[route_decision.route_id]
                    if route_decision.system_prompt_additions:
                        context.system_prompt_additions.append(
                            route_decision.system_prompt_additions
                        )
                    context.current_input = (
                        route_decision.user_input_transform or context.original_input
                    )
                    context.metadata.update(route_decision.metadata)

                    # Stream from next node
                    async for next_chunk in next_node.process_stream(
                        context.current_input, context
                    ):
                        yield next_chunk

            # Legacy routing
            elif self.next_node and (
                not self.condition or self.condition(complete_content)
            ):
                async for next_chunk in self.next_node.process_stream(complete_content):
                    yield next_chunk

        except Exception as e:
            logger.error(
                "stream_processing_error",
                error=str(e),
                node_id=id(self),
                input_length=len(str(input_data)),
            )
            # Yield error chunk
            yield StreamChunk(
                content="",
                done=True,
                metadata={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "node_id": id(self),
                },
            )

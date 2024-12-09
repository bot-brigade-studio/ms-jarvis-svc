import re
from typing import AsyncIterator, List, Optional, Dict, Any, Union, Tuple
from uuid import UUID
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import CreateMessageRequest
from app.utils.debug import debug_print
from app.utils.http_client import FrostClient, NexusClient
from app.core.config import settings
from app.models.bot import Bot, BotConfig
from app.repositories.bot_repository import BotConfigRepository, BotRepository
from app.core.exceptions import APIError
from chainable_llm.core.types import (
    InputType,
    LLMConfig,
    PromptConfig,
    StreamChunk,
    StreamConfig,
)
from chainable_llm.nodes.base import LLMNode
from uuid_extensions import uuid7
from app.models.base import current_user_id, current_tenant_id


class ConversationService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.bot_repo = BotRepository(Bot, db)
        self.bot_config_repo = BotConfigRepository(BotConfig, db)
        self.nexus_client = NexusClient()
        self.frost_client = FrostClient()
        
    async def process_user_message(
        self,
        bot_id: UUID,
        thread_id: UUID,
        schema: CreateMessageRequest,
        stream: bool = True,
    ):
        """Process a user message and handle streaming response."""
        if not stream:
            raise APIError(
                status_code=405,
                message="Non-streaming responses are not implemented yet",
            )

        config = await self._get_bot_config(bot_id)
        api_key, provider = self._get_api_key_and_provider(config.model_name)

        payload = self._create_payload(schema)

        user_message = await self._post_user_message(thread_id, payload)
        formatted_history = await self._get_formatted_history(
            thread_id=thread_id,
            bot_id=bot_id,
        )
        
        debug_print("formatted_history", formatted_history)

        credit_account = await self.frost_client.get(f"api/v1/credits/me")
        if credit_account.json()["data"]["balance"] < 5:
            raise APIError(status_code=402, message="Your credit account has insufficient balance")
        if credit_account.json()["data"]["status"] != "ACTIVE":
            raise APIError(status_code=402, message="Your Credit Account is not active")

        return self._handle_streaming_response(
            schema=schema,
            api_key=api_key,
            provider=provider,
            config=config,
            user_msg_id=user_message["id"],
            thread_id=thread_id,
            assistant_msg_id=schema.response_id,
            formatted_history=formatted_history,
            credit_account=credit_account.json()["data"],
        )

    async def stream_callback(chunk: StreamChunk, **kwargs):
        """Simple callback to print streaming chunks."""
        print(f"{chunk.content}", end="", flush=True)
        if chunk.done:
            print("\n--- Stream completed ---\n")

    async def _handle_streaming_response(
        self,
        schema: CreateMessageRequest,
        api_key: str,
        provider: str,
        config: BotConfig,
        thread_id: UUID,
        user_msg_id: str,
        assistant_msg_id: str,
        formatted_history: List[Dict[str, str]],
        credit_account: Dict[str, Any],
    ) -> Union[Dict[str, Any], AsyncIterator[StreamChunk]]:
        """Handle the streaming response from the LLM."""
        accumulated_content = []
        system_message = config.custom_instructions

        llm = self._initialize_llm(api_key, provider, config, system_message)

        for message in formatted_history[:-1]:
            llm.conversation.add_message(
                role=message["role"], content=message["content"]
            )

        async for chunk in llm.process_stream(schema.content):
            if chunk.content:
                accumulated_content.append(chunk.content)
            yield chunk

            if chunk.done:
                full_content = "".join(accumulated_content)
                await self._post_assistant_message(
                    thread_id, assistant_msg_id, full_content, user_msg_id
                )
                if len(formatted_history) == 1:
                    fist_two_messages = formatted_history
                    fist_two_messages.append({"role": "assistant", "content": full_content})
                    await self._update_thread_name(thread_id, fist_two_messages)
                usage = chunk.metadata.get("usage")
                request_id = str(uuid7())
                payload_usage = {
                    "account_id": credit_account["id"],
                    "model_name": config.model_name,
                    "input_tokens": usage.get("prompt_tokens"),
                    "output_tokens": usage.get("completion_tokens"),
                    "request_id": request_id,
                    "user_id": current_user_id.get(),
                    "tenant_id": current_tenant_id.get(),
                    "ip_address": "127.0.0.1",
                    "user_agent": "",
                }
                await self.frost_client.post(
                    "api/v1/events",
                    json=payload_usage,
                )
        
           
        
        await self.db.commit()
        
    async def _update_thread_name(self, thread_id: UUID, fist_two_messages: List[Dict[str, str]]):
        bot_config = BotConfig(
            model_name="gpt-4o-mini",
            temperature=0.0,
            max_output_tokens=1000,
        )
        input_msg = f"Create a title for this conversation: {fist_two_messages}"
        system_message = "You are a helpful assistant. Generate a concise title for the conversation."
        llm_summary = self._initialize_llm("", "openai", bot_config, system_message)
        title = await llm_summary.process(input_msg)

        await self.nexus_client.put(
            f"api/v1/threads/{thread_id}/name",
            json={"name": title.content},
        )

    def _get_api_key_and_provider(self, model_name: str) -> Tuple[str, str]:
        """Retrieve API key and provider based on model name."""
        # If model name contains "gpt" then OpenAI, if contains "claude" then Anthropic
        is_openai = "gpt" in model_name.lower()
        is_anthropic = "claude" in model_name.lower()

        if is_openai:
            return settings.OPENAI_API_KEY, "openai"
        elif is_anthropic:
            return settings.ANTHROPIC_API_KEY, "anthropic"
        else:
            raise APIError(status_code=400, message="Invalid model name")

    async def _get_formatted_history(
        self, thread_id: UUID, bot_id: UUID
    ) -> List[Dict[str, str]]:
        """Get formatted conversation history for LLM."""
        res = await self.nexus_client.get(
            f"api/v1/messages/{thread_id}",
            params={"skip": 0, "limit": 100, "group_by": str(bot_id)},
        )
        messages = res.json()["data"]
        return [
            {"role": message["role"], "content": message["content"]}
            for message in messages
        ]

    async def _get_bot_config(self, bot_id: UUID) -> BotConfig:
        """Retrieve the bot configuration."""
        bot = await self.bot_repo.get(filters={"id": bot_id}, select_fields=["id"])
        if not bot:
            raise APIError(status_code=404, message="Bot not found")

        config = await self.bot_config_repo.get(
            filters={
                "bot_id": bot_id,
                "is_current": True,
            },
        )
        if not config:
            raise APIError(status_code=404, message="Bot config not found")

        return config

    def _create_payload(self, schema: CreateMessageRequest) -> Dict[str, Any]:
        """Create payload for user message."""
        return {
            "content": schema.content,
            "role": "user",
            "id": schema.id if schema.id else str(uuid7()),
            "parent_id": schema.parent_id if schema.parent_id else None,
            "status": "completed",
        }

    async def _post_user_message(
        self, thread_id: UUID, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post user message to the server."""
        res = await self.nexus_client.post(
            f"api/v1/messages/{thread_id}",
            json=payload,
        )
        return res.json()["data"]

    async def _post_assistant_message(
        self, thread_id: UUID, assistant_msg_id: str, content: str, user_msg_id: str
    ):
        """Post assistant message to the server."""
        await self.nexus_client.post(
            f"api/v1/messages/{thread_id}",
            json={
                "id": assistant_msg_id,
                "content": content,
                "status": "completed",
                "parent_id": user_msg_id,
                "role": "assistant",
            },
        )

    def _initialize_llm(
        self, api_key: str, provider: str, config: BotConfig, system_message: str
    ) -> LLMNode:
        """Initialize the LLM node."""
        return LLMNode(
            llm_config=LLMConfig(
                provider=provider,
                api_key=api_key,
                model=config.model_name,
                temperature=config.temperature,
                max_tokens=config.max_output_tokens,
                streaming=StreamConfig(enabled=True, chunk_size=10),
                proxy_enabled=settings.BBPROXY_IS_ENABLED,
                proxy_url=settings.BBPROXY_LLM_URL,
                proxy_api_key=settings.BBPROXY_API_KEY,
            ),
            prompt_config=PromptConfig(
                input_type=InputType.USER_PROMPT,
                base_system_prompt=system_message,
                template="{input}",
            ),
        )

from typing import AsyncGenerator, List, Dict, Any, Union
from uuid import UUID
import json
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.chat import CreateMessageRequest
from app.utils.debug import debug_print
from app.utils.http_client import FrostClient, NexusClient
from app.models.bot import Bot, BotConfig
from app.repositories.bot_repository import BotConfigRepository, BotRepository
from app.core.exceptions import APIError
from botbrigade_llm import LLMClient
from uuid_extensions import uuid7


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

        payload = self._create_payload(schema)

        user_message = await self._post_user_message(thread_id, payload)
        formatted_history = await self._get_formatted_history(
            thread_id=thread_id,
            bot_id=bot_id,
        )
        system_message = config.custom_instructions
        formatted_history.insert(0, {"role": "system", "content": system_message})

        credit_account = await self.frost_client.get(f"api/v1/credits/me")
        credit_account_data = credit_account.json()["data"]
        if credit_account_data["balance"] < 0:
            raise APIError(
                status_code=402, message="Your credit account has insufficient balance"
            )
        if credit_account_data["status"] != "ACTIVE":
            raise APIError(status_code=402, message="Your Credit Account is not active")

        project_api_key = await self.frost_client.get(
            "api/v1/project-api-keys/me/current"
        )
        project_api_key_data = project_api_key.json()["data"]
        api_key = project_api_key_data["key"]

        return self._handle_streaming_response(
            api_key=api_key,
            user_msg_id=user_message["id"],
            thread_id=thread_id,
            assistant_msg_id=schema.response_id,
            formatted_history=formatted_history,
        )

    async def _handle_streaming_response(
        self,
        api_key: str,
        thread_id: UUID,
        user_msg_id: str,
        assistant_msg_id: str,
        formatted_history: List[Dict[str, str]],
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Handle the streaming response from the LLM."""
        accumulated_content = []

        llm_client = LLMClient(api_key=api_key)

        async for chunk in await llm_client.responses.acreate(
            model="claudia-1",
            messages=formatted_history,
            stream=True,
        ):
            if chunk:
                accumulated_content.append(chunk)
                yield chunk

                if chunk == "{}":
                    full_content = "".join(accumulated_content)
                    await self._post_assistant_message(
                        thread_id, assistant_msg_id, full_content, user_msg_id
                    )

                    if len(formatted_history) == 2:
                        # remove system message
                        formatted_history.pop(0)
                        fist_two_messages = formatted_history
                        fist_two_messages.append(
                            {"role": "assistant", "content": full_content}
                        )
                        await self._update_thread_name(
                            api_key, thread_id, fist_two_messages
                        )

    async def _update_thread_name(
        self, api_key: str, thread_id: UUID, fist_two_messages: List[Dict[str, str]]
    ):

        llm_client = LLMClient(api_key=api_key)
        response = llm_client.responses.create(
            model="claudia-1",
            messages=[
                {
                    "role": "user",
                    "content": "Generate a short and concise one-sentence title for the following conversation between a user and an assistant. Only return the sentence itself without quotation marks or any extra characters : "
                    + json.dumps(fist_two_messages),
                },
            ],
        )
        content = response["choices"][0]["message"]["content"]
        await self.nexus_client.put(
            f"api/v1/threads/{thread_id}/name",
            json={"name": content},
        )

    async def _get_formatted_history(
        self, thread_id: UUID, bot_id: UUID
    ) -> List[Dict[str, str]]:
        """Get formatted conversation history for LLM."""
        res = await self.nexus_client.get(
            f"api/v1/messages/{thread_id}",
            params={"skip": 0, "limit": 10, "group_by": str(bot_id)},
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
        payload = {
            "id": assistant_msg_id,
            "content": content,
            "status": "completed",
            "parent_id": user_msg_id,
            "role": "assistant",
        }
        await self.nexus_client.post(
            f"api/v1/messages/{thread_id}",
            json=payload,
        )

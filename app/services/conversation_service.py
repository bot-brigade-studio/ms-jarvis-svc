from typing import AsyncIterator, List, Optional, Dict, Any, Union, Tuple
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.http_client import NexusClient
from app.core.config import settings
from app.utils.debug import debug_print
from app.models.bot import Bot, BotConfig
from app.repositories.bot_repository import BotConfigRepository, BotRepository
from app.core.exceptions import APIError
from chainable_llm.core.types import StreamChunk
from chainable_llm.nodes.base import LLMNode


class ConversationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.bot_repo = BotRepository(Bot, db)
        self.bot_config_repo = BotConfigRepository(BotConfig, db)
        self.nexus_client = NexusClient()
        self.llm_node = LLMNode()

    async def process_user_message(
        self,
        thread_id: UUID,
        content: str,
        model_name: Optional[str] = None,
        stream: bool = False,
        parent_id: Optional[UUID] = None,
        id: Optional[UUID] = None,
        response_id: Optional[UUID] = None,
    ) -> Union[Dict[str, Any], AsyncIterator[StreamChunk]]:
        pass

    async def _get_bot_config(self, bot_id: UUID) -> BotConfig:
        bot = await self.bot_repo.get(filters={"id": bot_id}, select_fields=["id"])
        if not bot:
            raise APIError(status_code=404, message="Bot not found")

        config = await self.bot_config_repo.get(
            filters={
                "bot_id": bot_id,
                "is_current": True,
            },
            select_fields=["id"],
        )
        if not config:
            raise APIError(status_code=404, message="Bot config not found")

        return config

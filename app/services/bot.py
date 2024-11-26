from typing import Any, Dict
from fastapi import Depends
from sqlalchemy import UUID
from app.core.exceptions import APIError
from app.db.session import get_db
from app.models.bot import Bot, BotConfig, ConfigVariable
from app.models.master import MstItem
from app.repositories.bot_repository import (
    BotConfigRepository,
    BotRepository,
    ConfigVariableRepository,
)
from app.repositories.master_repository import MstItemRepository
from sqlalchemy.ext.asyncio import AsyncSession
import re

from app.schemas.bot import BotConfigCreate, BotCreate


class BotService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.bot_repo = BotRepository(Bot, db)
        self.bot_config_repo = BotConfigRepository(BotConfig, db)
        self.config_variable_repo = ConfigVariableRepository(ConfigVariable, db)
        self.mst_item_repo = MstItemRepository(MstItem, db)

    async def _validate_category(self, category_id: UUID):
        category = await self.mst_item_repo.get(
            filters={"id": category_id}, select_fields=["id"]
        )
        if not category:
            raise APIError(status_code=404, message="Category not found")

    async def create_bot(self, schema: BotCreate) -> Bot:
        is_exists = await self.bot_repo.get(
            filters={"name": schema.name}, select_fields=["id"]
        )
        if is_exists:
            raise APIError(status_code=400, message="Bot name already exists")

        if schema.category_id:
            await self._validate_category(schema.category_id)

        bot = await self.bot_repo.create(schema)

        return await self.bot_repo.get(
            filters={"id": bot.id}, load_options=["configs.variables"]
        )

    async def update_bot(self, id: UUID, schema: BotCreate) -> Bot:
        bot = await self.bot_repo.get(filters={"id": id}, select_fields=["id", "name"])
        if not bot:
            raise APIError(status_code=404, message="Bot not found")

        if schema.category_id:
            await self._validate_category(schema.category_id)

        if schema.name != bot.name:
            is_exists = await self.bot_repo.get(
                filters={"name": schema.name}, select_fields=["id"]
            )
            if is_exists:
                raise APIError(status_code=400, message="Bot name already exists")

        return await self.bot_repo.update(bot.id, schema)

    async def create_bot_config(
        self, bot_id: UUID, schema: BotConfigCreate
    ) -> BotConfig:
        bot_exists = await self.bot_repo.get(
            filters={"id": bot_id}, select_fields=["id"]
        )
        if not bot_exists:
            raise APIError(status_code=404, message="Bot not found")

        count = await self.bot_config_repo.count(filters={"bot_id": bot_id})
        is_current = count == 0

        config = await self.bot_config_repo.create(
            {
                **schema.model_dump(),
                "bot_id": bot_id,
                "version": count + 1,
                "is_current": is_current,
            }
        )

        await self.save_config_variables(config)

        return config

    async def update_bot_config(
        self, bot_id: UUID, config_id: UUID, schema: BotConfigCreate
    ) -> BotConfig:
        bot_config = await self.bot_config_repo.get(
            filters={"id": config_id, "bot_id": bot_id}, select_fields=["id"]
        )
        if not bot_config:
            raise APIError(status_code=404, message="Bot config not found")

        await self.config_variable_repo.delete(
            filters={"config_id": bot_config.id}, force=True
        )

        config = await self.bot_config_repo.update(bot_config.id, schema)

        await self.save_config_variables(config)

        return await self.bot_config_repo.get(
            filters={"id": config.id}, load_options=["variables"]
        )

    async def update_bot_config_is_current(self, id: UUID, bot_id: UUID):
        # update all other configs to not be current
        configs, _ = await self.bot_config_repo.get_multi(
            filters={"bot_id": bot_id}, select_fields=["id"]
        )
        for config in configs:
            if config.id != id:
                await self.bot_config_repo.update(config.id, {"is_current": False})

        # update this config to be current
        await self.bot_config_repo.update(id, {"is_current": True})

    async def save_config_variables(self, config: BotConfig):
        custom_instructions = config.custom_instructions
        if custom_instructions:
            variables = re.findall(r"{{(\w+)}}", custom_instructions)
            for variable in variables:
                await self.config_variable_repo.create(
                    {"key": variable, "value": None, "config_id": config.id}
                )
        else:
            await self.config_variable_repo.delete(
                filters={"config_id": config.id}, force=True
            )

    async def delete_bot_config(self, id: UUID):
        await self.config_variable_repo.delete(filters={"config_id": id}, force=True)
        await self.bot_config_repo.delete(filters={"id": id}, force=True)

    async def delete_bot(self, id: UUID):
        bot = await self.bot_repo.get(filters={"id": id}, select_fields=["id"])
        if not bot:
            raise APIError(status_code=404, message="Bot not found")

        configs, _ = await self.bot_config_repo.get_multi(
            filters={"bot_id": id}, select_fields=["id"]
        )
        for config in configs:
            await self.delete_bot_config(config.id)

        await self.bot_repo.delete(filters={"id": id}, force=True)

    async def get_bots(
        self, skip: int = 0, limit: int = 10, filters: Dict[str, Any] = None
    ):
        return await self.bot_repo.get_multi(skip=skip, limit=limit, filters=filters)

    async def get_bot(self, id: UUID):
        return await self.bot_repo.get(
            filters={"id": id}, load_options=["configs.variables", "category"]
        )

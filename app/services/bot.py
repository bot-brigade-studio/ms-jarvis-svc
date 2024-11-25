
from fastapi import Depends
from openai import APIError
from app.db.session import get_db
from app.models.bot import Bot, BotConfig, ConfigVariable
from app.repositories.bot_repository import BotConfigRepository, BotRepository, ConfigVariableRepository
from sqlalchemy.ext.asyncio import AsyncSession
import re

from app.schemas.bot import BotCreate
from app.utils.debug import debug_print

class BotService:
    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.bot_repo = BotRepository(Bot, db)
        self.bot_config_repo = BotConfigRepository(BotConfig, db)
        self.config_variable_repo = ConfigVariableRepository(ConfigVariable, db)
        
    async def create_bot(self, schema: BotCreate) -> Bot:
        is_exists = await self.bot_repo.get(filters={"name": schema.name})
        if is_exists:
            raise APIError(status_code=400, message="Bot name already exists")
        
        debug_print("schema", schema)
        
        data_bot = schema.model_dump(exclude={"config"})
        bot = await self.bot_repo.create(data_bot)
        
        data_config = schema.config.model_dump()
        data_config["bot_id"] = bot.id
        config = await self.bot_config_repo.create(data_config)
        
        custom_instructions = config.custom_instructions
        # check with pattern {{variable_name}}
        # if found, create config variable
        if custom_instructions:
            variables = re.findall(r"{{(\w+)}}", custom_instructions)
            for variable in variables:
                await self.config_variable_repo.create({"key": variable, "value": "", "config_id": config.id})
        
        return await self.bot_repo.get(filters={"id": bot.id}, load_options=["configs.variables"])
        
        
        
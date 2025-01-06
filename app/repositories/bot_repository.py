from app.core.repository import BaseRepository
from app.models.bot import Bot, BotConfig, ConfigVariable, TeamBotAccess

class BotRepository(BaseRepository[Bot, None, None]):
    pass

class BotConfigRepository(BaseRepository[BotConfig, None, None]):
    pass

class ConfigVariableRepository(BaseRepository[ConfigVariable, None, None]):
    pass

class TeamBotAccessRepository(BaseRepository[TeamBotAccess, None, None]):
    """Repository for managing team bot access"""
    pass
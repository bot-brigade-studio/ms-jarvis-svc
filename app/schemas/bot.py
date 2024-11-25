
from typing import Optional
from app.schemas.base import BaseSchema
from app.models.enums import StatusEnum
from pydantic import BaseModel, Field
from typing import List

class BotBase(BaseModel):
    name: str
    avatar_url: Optional[str] = None
    tagline: Optional[str] = None
    description: Optional[str] = None
    greeting: Optional[str] = None
    is_bot_definition_public: bool
    status: StatusEnum

    
class BotConfigVariableBase(BaseModel):
    key: str
    value: dict
    
class BotConfigBase(BaseModel):
    name: str = "Default"
    model_name: str
    custom_instructions: Optional[str] = None
    max_context_tokens: int = 4000
    max_output_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 0
    is_current: bool = True
    version: int = 1

class BotCreate(BotBase):
    pass

class BotConfigCreate(BotConfigBase):
    pass

class BotConfigVariableResponse(BotConfigVariableBase, BaseSchema):
    pass

class BotConfigResponse(BotConfigBase, BaseSchema):
    variables: List[BotConfigVariableResponse]
    
class BotResponse(BotBase, BaseSchema):
    configs: List[BotConfigResponse]
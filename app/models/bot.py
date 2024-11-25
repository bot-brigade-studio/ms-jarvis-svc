# app/models/bot.py

from sqlalchemy import Column, Float, Integer, String, Boolean, ForeignKey, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import TenantSoftDeleteModel
from app.models.enums import StatusEnum

class Bot(TenantSoftDeleteModel):
    __tablename__ = "bots"
    
    name = Column(String(255), nullable=False) # eg. "Writing Academics"
    avatar_url = Column(String(255)) # eg. "https://example.com/avatar.png"
    tagline = Column(String(255)) # eg. "Helping academics write better."
    description = Column(Text) # eg. "This bot helps academics write better."
    greeting = Column(Text) # eg. "Hello! How can I assist you today?"
    
    is_bot_definition_public = Column(Boolean, default=False) # if true, public users can see the bot definition including the parameters and variables
    status = Column(SQLAlchemyEnum(StatusEnum), default=StatusEnum.ACTIVE)
    
    # Relationships
    configs = relationship("BotConfig", back_populates="bot")

class BotConfig(TenantSoftDeleteModel):
    __tablename__ = "bot_configs"
    
    is_current = Column(Boolean, default=True) # if true, this is the current parameters for the bot
    version = Column(Integer, default=1) # incremented when parameters are updated
    name = Column(String(255), default="Default") # e.g. "Default"
    model_name = Column(String(255), nullable=False) # e.g. gpt-4o, claude-3-5-sonnet-20240620
    custom_instructions = Column(Text) # e.g. "You are a helpful assistant."
    max_context_tokens = Column(Integer, default=4000) # e.g. 4000
    max_output_tokens = Column(Integer, default=4000) # e.g. 4000
    temperature = Column(Float, default=0.7) # e.g. 0.7
    top_p = Column(Float, default=1.0) # e.g. 1.0
    top_k = Column(Integer, default=0) # e.g. 0


    # Relationships
    bot_id = Column(UUID(as_uuid=True), ForeignKey("bots.id"))
    bot = relationship("Bot", back_populates="configs")
    variables = relationship("ConfigVariable", back_populates="config")
    
class ConfigVariable(TenantSoftDeleteModel):
    __tablename__ = "config_variables"
    
    key = Column(String(255)) # eg. "academic_level"
    value = Column(JSONB) # eg. {"type": "string", "value": "PhD"}
    config_id = Column(UUID(as_uuid=True), ForeignKey("bot_configs.id"))
    
    # Relationships
    config = relationship("BotConfig", back_populates="variables")

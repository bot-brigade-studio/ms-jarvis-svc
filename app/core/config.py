from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    API_V1_STR: str
    SECRET_KEY: str
    DATABASE_URL: str
    ENVIRONMENT: str
    DEBUG : bool = True

    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    class Config:
        env_file = ".env"

settings = Settings()
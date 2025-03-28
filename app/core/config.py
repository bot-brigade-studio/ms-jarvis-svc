from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Project Settings
    PROJECT_NAME: str
    PROJECT_DESCRIPTION: str
    VERSION: str
    API_V1_STR: str
    ROOT_PATH: str

    # Database Settings
    DATABASE_URL: str
    ENVIRONMENT: str

    # API Key Providers
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str

    # Services
    HEIMDALL_SERVICE_URL: str
    SANCTUM_SERVICE_URL: str
    NEXUS_SERVICE_URL: str
    FROST_SERVICE_URL: str
    FURY_SERVICE_URL: str

    # S3
    BUCKET_NAME: str = "jarvis-service-bucket"

    # PROXY
    BBPROXY_IS_ENABLED: bool = False
    BBPROXY_LLM_URL: str = ""
    BBPROXY_API_KEY: str = ""

    # API Key Encryption Configuration
    PUBLIC_KEY_PATH: Optional[str] = None
    PRIVATE_KEY_PATH: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()

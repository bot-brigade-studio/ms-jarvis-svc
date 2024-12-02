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
    HEIMDALL_SERVICE_URL: str = "https://api-shield.botbrigade.tech/heimdall"
    SANCTUM_SERVICE_URL: str = "https://api-shield.botbrigade.tech/sanctum"
    NEXUS_SERVICE_URL: str = "https://api-shield.botbrigade.tech/nexus"
    FROST_SERVICE_URL: str = "https://api-shield.botbrigade.tech/frost"
    # S3
    BUCKET_NAME: str = "jarvis-service-bucket"

    class Config:
        env_file = ".env"


settings = Settings()

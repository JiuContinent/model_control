import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent  # app directory
ENV_FILE = BASE_DIR / ".env"                # src/app/.env

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    PROJECT_NAME: str = "My FastAPI Project"
    USE_MONGO: bool = False
    MONGO_URI: str = "mongodb://localhost:27017/"
    MONGO_DB_NAME: str = "model_control_db"
    
    # Multi-datasource configuration
    MAVLINK_MONGO_URI: str = "mongodb://localhost:27017/"
    MAVLINK_MONGO_DB_NAME: str = "model_control_mavlink"
    
    CHAT_MONGO_URI: str = "mongodb://localhost:27017/"
    CHAT_MONGO_DB_NAME: str = "model_control_chat"
    
    ANALYTICS_MONGO_URI: str = "mongodb://localhost:27017/"
    ANALYTICS_MONGO_DB_NAME: str = "model_control_analytics"
    
    OPENAI_API_KEY: str = "dummy_key"
    OPENAI_API_BASE: str | None = None
    
    # Add environment variable validation
    def model_post_init(self, __context) -> None:
        if self.OPENAI_API_KEY == "dummy_key":
            print("Warning: Please set a valid OPENAI_API_KEY")
        if not self.USE_MONGO:
            print("Warning: No database enabled, some features may not be available")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

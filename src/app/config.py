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
    
    # MongoDB 认证配置
    MONGO_HOST: str = "221.226.33.58"
    MONGO_PORT: int = 27017
    MONGO_USERNAME: str = "root"
    MONGO_PASSWORD: str = "RedFlym3o6n9@&#"
    MONGO_AUTH_SOURCE: str = "admin"
    
    # 主数据库配置
    MONGO_DB_NAME: str = "control_db"
    
    # 多数据库配置 - 支持control_db和dji等多个数据库
    DJI_DB_NAME: str = "dji"
    CONTROL_DB_NAME: str = "control_db"
    
    # Multi-datasource configuration
    MAVLINK_MONGO_DB_NAME: str = "control_mavlink"
    CHAT_MONGO_DB_NAME: str = "model_control_chat"
    ANALYTICS_MONGO_DB_NAME: str = "ai_control_analytics"
    
    OPENAI_API_KEY: str = "dummy_key"
    OPENAI_API_BASE: str | None = None
    
    @property
    def MONGO_URI(self) -> str:
        """动态构建MongoDB URI，支持认证"""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            # 有认证信息的URI
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/?authSource={self.MONGO_AUTH_SOURCE}"
        else:
            # 无认证的URI
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/"
    
    @property
    def MAVLINK_MONGO_URI(self) -> str:
        """MAVLink数据源的MongoDB URI"""
        return self.MONGO_URI
    
    @property
    def CHAT_MONGO_URI(self) -> str:
        """Chat数据源的MongoDB URI"""
        return self.MONGO_URI
    
    @property
    def ANALYTICS_MONGO_URI(self) -> str:
        """Analytics数据源的MongoDB URI"""
        return self.MONGO_URI
    
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

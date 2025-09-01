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
    
    # MongoDB基本配置
    MONGO_HOST: str = "221.226.33.58"
    MONGO_PORT: int = 27017
    MONGO_USERNAME: str = "root"
    MONGO_PASSWORD: str = "RedFlym3o6n9@&#"
    MONGO_AUTH_DB: str = "admin"  # 认证数据库，通常是admin
    MONGO_DB_NAME: str = "ai_control_db"
    
    # Multi-datasource configuration
    MAVLINK_MONGO_DB_NAME: str = "model_control_mavlink"
    CHAT_MONGO_DB_NAME: str = "model_control_chat"
    ANALYTICS_MONGO_DB_NAME: str = "model_control_analytics"
    
    # MySQL数据库配置
    USE_MYSQL: bool = True
    MYSQL_HOST: str = "221.226.33.58"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "RedFlym3y6s9@&#"
    MYSQL_CHARSET: str = "utf8mb4"
    
    # MySQL多租户数据库配置
    MYSQL_TENANT_2_DB: str = "2_tenant"
    MYSQL_TENANT_3_DB: str = ""  # 空字符串表示未启用
    MYSQL_RUOYI_VUE_PRO_DB: str = ""  # 空字符串表示未启用
    
    # 默认MySQL数据库
    MYSQL_DEFAULT_DB: str = "2_tenant"
    
    OPENAI_API_KEY: str = "dummy_key"
    OPENAI_API_BASE: str | None = None
    
    @property
    def MONGO_URI(self) -> str:
        """动态生成MongoDB连接URI"""
        if self.MONGO_USERNAME and self.MONGO_PASSWORD:
            # 有认证的URI
            return f"mongodb://{self.MONGO_USERNAME}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_AUTH_DB}"
        else:
            # 无认证的URI
            return f"mongodb://{self.MONGO_HOST}:{self.MONGO_PORT}/"
    
    @property
    def MAVLINK_MONGO_URI(self) -> str:
        """MAVLink MongoDB连接URI"""
        return self.MONGO_URI
    
    @property
    def CHAT_MONGO_URI(self) -> str:
        """Chat MongoDB连接URI"""
        return self.MONGO_URI
    
    @property
    def ANALYTICS_MONGO_URI(self) -> str:
        """Analytics MongoDB连接URI"""
        return self.MONGO_URI
    
    # Add environment variable validation
    def model_post_init(self, __context) -> None:
        if self.OPENAI_API_KEY == "dummy_key":
            print("Warning: Please set a valid OPENAI_API_KEY")
        if not self.USE_MONGO and not self.USE_MYSQL:
            print("Warning: No database enabled, some features may not be available")
        if self.USE_MYSQL and not self.MYSQL_PASSWORD:
            print("Warning: MySQL password is empty, please check MySQL configuration")
        if self.USE_MONGO and not self.MONGO_USERNAME:
            print("Warning: MongoDB username is empty, will use connection without authentication")
        if self.USE_MONGO and self.MONGO_USERNAME and not self.MONGO_PASSWORD:
            print("Warning: MongoDB password is empty but username is set")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent  # app directory
PROJECT_ROOT = BASE_DIR.parent.parent       # project root directory

# 支持多个.env文件位置
ENV_FILES = [
    PROJECT_ROOT / ".env",                  # 项目根目录的.env
    BASE_DIR / ".env",                      # src/app/.env
]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(env_file) for env_file in ENV_FILES if env_file.exists()],
        env_file_encoding='utf-8',
        extra='ignore'
    )

    PROJECT_NAME: str = "Model Control AI System"
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
    
    # vLLM配置
    VLLM_BASE_URL: str = "http://221.226.33.59:2800"
    VLLM_TIMEOUT: int = 30
    VLLM_DEFAULT_MODEL: str = "default"
    
    # MCP协议配置
    MCP_ENABLED: bool = True
    MCP_SERVER_NAME: str = "Model Control MCP Server"
    MCP_SERVER_VERSION: str = "1.0.0"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/app.log"
    LOG_ROTATION: str = "50 MB"
    LOG_RETENTION: str = "30 days"
    DEBUG: bool = False
    
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
        # 延迟导入避免循环依赖
        try:
            from loguru import logger
            
            if not self.USE_MONGO:
                logger.warning("No database enabled, some features may not be available")
            
            # vLLM服务验证
            if not self.VLLM_BASE_URL:
                logger.warning("VLLM_BASE_URL not configured, LLM features will not be available")
                
        except ImportError:
            # 如果日志系统还未初始化，使用 print
            if not self.USE_MONGO:
                print("Warning: No database enabled, some features may not be available")
            if not self.VLLM_BASE_URL:
                print("Warning: VLLM_BASE_URL not configured, LLM features will not be available")


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()

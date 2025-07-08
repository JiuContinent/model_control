# src/app/config.py
"""
应用配置管理
使用 pydantic-settings 从环境变量或 .env 文件中加载配置。
提供类型安全的全局配置对象 `settings`。
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    # Pydantic-Settings 配置
    model_config = SettingsConfigDict(
        env_file='.env',                # 从 .env 文件加载
        env_file_encoding='utf-8',
        extra='ignore'                  # 忽略 .env 中多余的变量
    )

    # 项目配置
    PROJECT_NAME: str = "My FastAPI Project"

    # MySQL 数据库配置
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_SERVER: str
    MYSQL_PORT: int
    MYSQL_DB: str
    USE_MYSQL: bool = False
    USE_MONGO: bool = False

    @property
    def MYSQL_ASYNC_URL(self) -> str:
        """
        生成异步 SQLAlchemy DSN (Data Source Name).
        格式: driver+async_driver://user:password@host:port/database
        """
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DB}"

    # MongoDB 配置
    MONGO_URI: str
    MONGO_DB_NAME: str

    # AI 后端配置
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str | None = None


@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
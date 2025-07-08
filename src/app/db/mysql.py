# src/app/db/mysql.py
"""
MySQL 异步数据库连接和会话管理。
"""
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings
from urllib.parse import quote_plus

# --- 1. 构建连接字符串（防止密码中的特殊字符出错） ---
encoded_password = quote_plus(settings.MYSQL_PASSWORD)

MYSQL_ASYNC_URL = (
    f"mysql+aiomysql://{settings.MYSQL_USER}:{encoded_password}"
    f"@{settings.MYSQL_SERVER}:{settings.MYSQL_PORT}/{settings.MYSQL_DB}"
)

# --- 2. 创建异步数据库引擎 ---
#     - echo=True 会打印所有执行的 SQL 语句，便于调试。生产环境建议关闭。
async_engine = create_async_engine(
    MYSQL_ASYNC_URL,
    echo=False,
    future=True
)

# --- 3. 创建异步会话工厂 ---
#     - expire_on_commit=False 防止在提交后 ORM 对象过期，在 FastAPI 中常用。
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

# --- 4. 获取数据库会话 ---
async def get_db_session() -> AsyncGenerator[AsyncSession | Any, Any]:
    """
    FastAPI 依赖项，用于获取和管理每个请求的数据库会话。
    使用 `async with` 语句确保会话在使用后能被正确关闭。
    """
    async with AsyncSessionLocal() as session:
        yield session

# --- 5. 关闭连接池 ---
async def close_mysql_connection():
    """在应用关闭时，释放数据库连接池。"""
    await async_engine.dispose()

# src/app/db/mongo_models.py
"""
MongoDB 异步数据库连接和 Beanie 初始化。
"""
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.config import settings
from app.models.mongo_models import ChatHistory  # 导入所有 Beanie 模型


async def init_mongo_db():
    """
    在应用启动时初始化 MongoDB 连接和 Beanie ODM。
    """
    print("Initializing MongoDB and Beanie...")
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client[settings.MONGO_DB_NAME]

    # 将所有需要被 Beanie 管理的 Document 模型放入 document_models 列表
    await init_beanie(
        database=db,
        document_models=[ChatHistory]
    )
    print("MongoDB and Beanie initialized.")
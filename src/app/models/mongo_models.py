# src/app/models/mongo_models.py
"""
Beanie ODM (Object-Document Mapper) 模型。
定义了 MongoDB 集合的结构。
"""
from beanie import Document
from pydantic import Field
from datetime import datetime

class ChatHistory(Document):
    user_id: str
    message: str
    reply: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        # 集合名称
        name = "chat_histories"
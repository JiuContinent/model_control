# src/app/models/schemas.py
"""
Pydantic 模型，用于数据校验、序列化和反序列化。
定义了 API 请求体和响应体的结构。
"""
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional
import uuid


# --- CRUD (Item) Schemas ---
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")


class ItemCreate(ItemBase):
    pass


class ItemSchema(ItemBase):
    id: str = Field(..., description="Unique item ID")

    # model_config 用于配置 Pydantic 的行为
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象（如 SQLAlchemy 模型）自动映射字段
    )


# --- AI Chat Schemas ---
class AIChatRequest(BaseModel):
    user_id: str = Field(..., description="The user's unique identifier")
    message: str = Field(..., description="The user's message to the AI")


class AIChatResponse(BaseModel):
    reply: str = Field(..., description="The AI's response")


# --- AI Control Schemas ---
class ControlCommandRequest(BaseModel):
    device_id: str = Field(..., description="The target device ID")
    command: str = Field(..., description="The command to execute (e.g., 'start_scan', 'rotate_left')")
    parameters: dict = Field({}, description="Additional parameters for the command")


class ControlCommandResponse(BaseModel):
    status: str = Field(..., description="The result status (e.g., 'success', 'failed')")
    detail: str | None = None
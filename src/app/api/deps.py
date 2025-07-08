# src/app/api/deps.py
"""
依赖注入提供者 (Dependency Providers)。
这些函数负责创建和提供 API 路由所需的各种服务实例。
使用 FastAPI 的 `Depends` 系统可以轻松地管理和模拟这些依赖项，便于测试。
"""
from functools import lru_cache

from fastapi import Depends

from app.config import get_settings, Settings, settings
from app.services.crud_service import CrudService
from app.services.ai_service import AIService
from app.ai_backends.openai_client import OpenAIClient
from app.ai_backends.device_control import DeviceController

# --- Singleton Dependencies (created once) ---

# @lru_cache()
# def get_connection_manager() -> connection_manager.__class__:
#     """提供一个全局单例的 ConnectionManager"""
#     return connection_manager

@lru_cache()
def get_openai_client(settings: Settings = get_settings()) -> OpenAIClient:
    """提供一个全局单例的 OpenAIClient"""
    return OpenAIClient(
        api_key=settings.OPENAI_API_KEY,
        api_base=settings.OPENAI_API_BASE,
    )

@lru_cache()
def get_device_controller() -> DeviceController:
    """提供一个全局单例的 DeviceController"""
    return DeviceController()

# --- Scoped Dependencies (created per request/call) ---

# def get_chat_service(
#     manager: connection_manager.__class__ = Depends(get_connection_manager)
# ) -> ChatService:
#     """提供一个 ChatService 实例，它依赖于 ConnectionManager"""
#     return ChatService(manager=manager)

def get_crud_service() -> CrudService:
    """提供一个 CrudService 实例"""
    return CrudService()

def get_ai_service(
    openai_client: OpenAIClient = Depends(get_openai_client),
    device_controller: DeviceController = Depends(get_device_controller)
) -> AIService:
    """提供一个 AIService 实例，它依赖于多个 AI 后端"""
    return AIService(
        openai_client=openai_client,
        device_controller=device_controller,
    )

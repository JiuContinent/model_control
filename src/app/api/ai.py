# src/app/api/ai.py
"""
API 路由 - AI 相关功能，包括聊天和设备控制
"""
from fastapi import APIRouter, Depends
from app.services.ai_service import AIService
from app.models.schemas import (
    AIChatRequest, AIChatResponse,
    ControlCommandRequest, ControlCommandResponse
)
from app.api.deps import get_ai_service

router = APIRouter()

@router.post("/chat", response_model=AIChatResponse)
async def handle_ai_chat(
    request: AIChatRequest,
    service: AIService = Depends(get_ai_service)
):
    """与 AI 大模型进行聊天"""
    reply = await service.process_chat(request)
    return AIChatResponse(reply=reply)


@router.post("/control", response_model=ControlCommandResponse)
async def handle_device_control(
    request: ControlCommandRequest,
    service: AIService = Depends(get_ai_service)
):
    """发送控制指令到设备"""
    result = await service.execute_control_command(request)
    return result

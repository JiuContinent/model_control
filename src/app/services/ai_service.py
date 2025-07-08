# src/app/services/ai_service.py
"""
封装所有与 AI 相关的业务逻辑，如聊天、控制等。
它协调 AI 后端客户端和数据模型。
"""
from app.ai_backends.openai_client import OpenAIClient
from app.ai_backends.device_control import DeviceController
from app.models.schemas import AIChatRequest, ControlCommandRequest
from app.models.mongo_models import ChatHistory


class AIService:
    def __init__(self, openai_client: OpenAIClient, device_controller: DeviceController):
        self.openai_client = openai_client
        self.device_controller = device_controller

    async def process_chat(self, chat_request: AIChatRequest) -> str:
        """处理 AI 聊天请求，获取回复并保存历史记录"""
        reply = await self.openai_client.get_chat_completion(
            user_id=chat_request.user_id,
            message=chat_request.message
        )

        # 将对话历史异步保存到 MongoDB
        history_record = ChatHistory(
            user_id=chat_request.user_id,
            message=chat_request.message,
            reply=reply
        )
        await history_record.insert()

        return reply

    async def execute_control_command(self, command_request: ControlCommandRequest) -> dict:
        """执行设备控制指令"""
        result = await self.device_controller.send_command(command_request)
        # 可以在这里增加日志记录到 MongoDB 的逻辑
        return result
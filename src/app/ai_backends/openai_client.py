# src/app/ai_backends/openai_client.py
"""
封装与 OpenAI API 交互的客户端。
"""
import openai
from app.config import Settings

class OpenAIClient:
    def __init__(self, settings: Settings):
        self.client = openai.AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )

    async def get_chat_completion(self, user_id: str, message: str) -> str:
        """调用 OpenAI Chat Completion API"""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": message}],
                user=user_id, # 用于监控和防止滥用
            )
            return response.choices[0].message.content or "Sorry, I couldn't get a response."
        except Exception as e:
            print(f"Error calling OpenAI: {e}")
            return "An error occurred while communicating with the AI service."
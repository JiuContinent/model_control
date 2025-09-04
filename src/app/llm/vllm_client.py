"""
vLLM客户端模块
用于调用远程vLLM服务进行文本生成和聊天
"""
from math import log
import httpx
import asyncio
import json
from typing import Dict, List, Optional, AsyncGenerator, Any
from pydantic import BaseModel

from app.core.exceptions import ModelControlException


class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str  # "user", "assistant", "system"
    content: str


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048
    stream: Optional[bool] = False


class ChatResponse(BaseModel):
    """聊天响应模型"""
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None


class vLLMClient:
    """vLLM服务客户端"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        初始化vLLM客户端
        
        Args:
            base_url: vLLM服务的基础URL
            timeout: 请求超时时间
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """获取可用模型列表"""
        try:
            response = await self.client.get(f"{self.base_url}/v1/models")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except httpx.RequestError as e:
            raise ModelControlException(f"Failed to connect to vLLM service: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelControlException(f"vLLM service error: {e.response.status_code}")
    
    async def health_check(self) -> bool:
        """检查vLLM服务健康状态"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        执行聊天完成
        
        Args:
            request: 聊天请求
            
        Returns:
            ChatResponse: 聊天响应
        """
        try:
            # 构建请求数据
            payload = {
                "model": request.model or "default",
                "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": request.stream
            }
            
            if request.stream:
                return await self._stream_chat_completion(payload)
            else:
                return await self._non_stream_chat_completion(payload)
                
        except httpx.RequestError as e:
            raise ModelControlException(f"Failed to connect to vLLM service: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelControlException(f"vLLM service error: {e.response.status_code}")
    
    async def _non_stream_chat_completion(self, payload: Dict) -> ChatResponse:
        """非流式聊天完成"""
        response = await self.client.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        data = response.json()
        
        # 解析响应
        choice = data["choices"][0]
        content = choice["message"]["content"]
        model = data.get("model", "unknown")
        usage = data.get("usage")
        
        return ChatResponse(content=content, model=model, usage=usage)
    
    async def _stream_chat_completion(self, payload: Dict) -> AsyncGenerator[str, None]:
        """流式聊天完成"""
        payload["stream"] = True
        
        async with self.client.stream(
            "POST",
            f"{self.base_url}/v1/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # 移除 "data: " 前缀
                    
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        choice = data["choices"][0]
                        delta = choice.get("delta", {})
                        
                        if "content" in delta:
                            yield delta["content"]
                    except json.JSONDecodeError:
                        continue
    
    async def generate_completion(self, prompt: str, model: Optional[str] = None, 
                                temperature: float = 0.7, max_tokens: int = 2048) -> str:
        """
        生成文本完成
        
        Args:
            prompt: 输入提示
            model: 模型名称
            temperature: 温度参数
            max_tokens: 最大token数
            
        Returns:
            str: 生成的文本
        """
        try:
            payload = {
                "model": model or "default",
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = await self.client.post(
                f"{self.base_url}/v1/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["text"]
            
        except httpx.RequestError as e:
            raise ModelControlException(f"Failed to connect to vLLM service: {e}")
        except httpx.HTTPStatusError as e:
            raise ModelControlException(f"vLLM service error: {e.response.status_code}")


class vLLMService:
    """vLLM服务管理器"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self._client: Optional[vLLMClient] = None
    
    async def get_client(self) -> vLLMClient:
        """获取vLLM客户端实例"""
        if self._client is None:
            self._client = vLLMClient(self.base_url)
        return self._client
    
    async def close(self):
        """关闭服务"""
        if self._client:
            await self._client.close()
            self._client = None
    
    async def is_healthy(self) -> bool:
        """检查服务健康状态"""
        try:
            client = await self.get_client()
            return await client.health_check()
        except:
            return False


# 全局vLLM服务实例
vllm_service: Optional[vLLMService] = None


def get_vllm_service() -> vLLMService:
    """获取全局vLLM服务实例"""
    global vllm_service
    if vllm_service is None:
        from app.config import settings
        vllm_service = vLLMService(settings.VLLM_BASE_URL)
    return vllm_service

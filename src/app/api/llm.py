"""
LLM API路由
提供vLLM服务调用和MCP协议交互的API接口
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional
import json
import asyncio
from datetime import datetime

from app.llm.vllm_client import (
    vLLMClient, ChatMessage, ChatRequest, ChatResponse, get_vllm_service
)
from app.mcp.protocol import (
    MCPClient, MCPServer, MCPMessage, MCPResource, MCPTool, MCPPrompt,
    get_mcp_server
)
from app.core.exceptions import ModelControlException

router = APIRouter(tags=["LLM"])


# 依赖注入函数
async def get_vllm_client():
    """获取vLLM客户端"""
    try:
        service = get_vllm_service()
        return await service.get_client()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get vLLM client: {e}")


async def get_mcp_server_instance():
    """获取MCP服务器实例"""
    return get_mcp_server()


@router.get("/llm/health")
async def check_llm_health():
    """检查LLM服务健康状态"""
    try:
        service = get_vllm_service()
        is_healthy = await service.is_healthy()
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "vLLM"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/llm/models")
async def list_models(client: vLLMClient = Depends(get_vllm_client)):
    """获取可用模型列表"""
    try:
        models = await client.list_models()
        return {
            "models": models,
            "total": len(models),
            "timestamp": datetime.now().isoformat()
        }
    except ModelControlException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/chat/completions")
async def chat_completions(
    request: ChatRequest,
    client: vLLMClient = Depends(get_vllm_client)
):
    """聊天完成API"""
    try:
        if request.stream:
            # 流式响应
            async def stream_generator():
                try:
                    async for chunk in client._stream_chat_completion({
                        "model": request.model or "default",
                        "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
                        "temperature": request.temperature,
                        "max_tokens": request.max_tokens,
                        "stream": True
                    }):
                        # 格式化为SSE格式
                        data = {
                            "id": f"chatcmpl-{datetime.now().timestamp()}",
                            "object": "chat.completion.chunk",
                            "created": int(datetime.now().timestamp()),
                            "model": request.model or "default",
                            "choices": [{
                                "index": 0,
                                "delta": {"content": chunk},
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(data)}\n\n"
                    
                    # 发送结束标记
                    yield "data: [DONE]\n\n"
                    
                except Exception as e:
                    error_data = {
                        "error": {
                            "message": str(e),
                            "type": "internal_error"
                        }
                    }
                    yield f"data: {json.dumps(error_data)}\n\n"
            
            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        else:
            # 非流式响应
            response = await client.chat_completion(request)
            return {
                "id": f"chatcmpl-{datetime.now().timestamp()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": response.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response.content
                    },
                    "finish_reason": "stop"
                }],
                "usage": response.usage
            }
    except ModelControlException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/completions")
async def text_completions(
    prompt: str,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    client: vLLMClient = Depends(get_vllm_client)
):
    """文本完成API"""
    try:
        result = await client.generate_completion(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return {
            "id": f"cmpl-{datetime.now().timestamp()}",
            "object": "text_completion",
            "created": int(datetime.now().timestamp()),
            "model": model or "default",
            "choices": [{
                "text": result,
                "index": 0,
                "finish_reason": "stop"
            }]
        }
    except ModelControlException as e:
        raise HTTPException(status_code=500, detail=str(e))


# MCP协议相关API
@router.get("/mcp/resources")
async def list_mcp_resources(server: MCPServer = Depends(get_mcp_server_instance)):
    """列出MCP资源"""
    try:
        # 使用服务器的内部资源列表
        resources = list(server.resources.values())
        return {
            "resources": [
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType
                }
                for resource in resources
            ],
            "total": len(resources)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcp/tools")
async def list_mcp_tools(server: MCPServer = Depends(get_mcp_server_instance)):
    """列出MCP工具"""
    try:
        tools = list(server.tools.values())
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in tools
            ],
            "total": len(tools)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcp/tools/{tool_name}/call")
async def call_mcp_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    server: MCPServer = Depends(get_mcp_server_instance)
):
    """调用MCP工具"""
    try:
        if tool_name not in server.tools:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # 构建MCP消息
        message = MCPMessage(
            method="tools/call",
            params={
                "name": tool_name,
                "arguments": arguments
            }
        )
        
        response = await server.handle_message(message)
        
        if response.error:
            raise HTTPException(status_code=500, detail=response.error.message)
        
        return response.result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mcp/prompts")
async def list_mcp_prompts(server: MCPServer = Depends(get_mcp_server_instance)):
    """列出MCP提示模板"""
    try:
        prompts = list(server.prompts.values())
        return {
            "prompts": [
                {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": prompt.arguments
                }
                for prompt in prompts
            ],
            "total": len(prompts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcp/prompts/{prompt_name}")
async def get_mcp_prompt(
    prompt_name: str,
    arguments: Optional[Dict[str, Any]] = None,
    server: MCPServer = Depends(get_mcp_server_instance)
):
    """获取MCP提示模板"""
    try:
        if prompt_name not in server.prompts:
            raise HTTPException(status_code=404, detail=f"Prompt {prompt_name} not found")
        
        # 构建MCP消息
        message = MCPMessage(
            method="prompts/get",
            params={
                "name": prompt_name,
                "arguments": arguments or {}
            }
        )
        
        response = await server.handle_message(message)
        
        if response.error:
            raise HTTPException(status_code=500, detail=response.error.message)
        
        return response.result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcp/message")
async def handle_mcp_message(
    message: Dict[str, Any],
    server: MCPServer = Depends(get_mcp_server_instance)
):
    """处理原始MCP消息"""
    try:
        mcp_message = MCPMessage(**message)
        response = await server.handle_message(mcp_message)
        
        return {
            "jsonrpc": response.jsonrpc,
            "id": response.id,
            "result": response.result,
            "error": response.error.dict() if response.error else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 组合功能：使用MCP协议增强的聊天
@router.post("/llm/chat/enhanced")
async def enhanced_chat(
    messages: List[ChatMessage],
    model: Optional[str] = None,
    use_mcp_tools: bool = False,
    use_mcp_prompts: bool = False,
    client: vLLMClient = Depends(get_vllm_client),
    server: MCPServer = Depends(get_mcp_server_instance)
):
    """增强的聊天功能，集成MCP协议"""
    try:
        # 如果启用MCP提示，可以预处理消息
        processed_messages = messages
        
        if use_mcp_prompts and server.prompts:
            # 这里可以添加提示模板处理逻辑
            pass
        
        # 构建聊天请求
        chat_request = ChatRequest(
            messages=processed_messages,
            model=model,
            temperature=0.7,
            max_tokens=2048
        )
        
        # 调用vLLM进行聊天
        response = await client.chat_completion(chat_request)
        
        # 如果启用MCP工具，可以进行后处理
        if use_mcp_tools and server.tools:
            # 这里可以添加工具调用逻辑
            # 例如：分析响应内容，判断是否需要调用工具
            pass
        
        return {
            "content": response.content,
            "model": response.model,
            "usage": response.usage,
            "mcp_enhanced": True,
            "timestamp": datetime.now().isoformat()
        }
        
    except ModelControlException as e:
        raise HTTPException(status_code=500, detail=str(e))


# 系统状态和配置
@router.get("/llm/status")
async def get_llm_status():
    """获取LLM系统状态"""
    try:
        service = get_vllm_service()
        mcp_server = get_mcp_server()
        
        vllm_healthy = await service.is_healthy()
        
        return {
            "vllm": {
                "status": "healthy" if vllm_healthy else "unhealthy",
                "base_url": service.base_url
            },
            "mcp": {
                "status": "active",
                "resources_count": len(mcp_server.resources),
                "tools_count": len(mcp_server.tools),
                "prompts_count": len(mcp_server.prompts)
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# vLLM 和 MCP 协议集成指南

## 概述

本项目已集成 vLLM 大语言模型服务和 MCP (Model Context Protocol) 协议，提供强大的 AI 对话和文本生成功能。

## 配置

### 1. vLLM 服务配置

在 `src/app/config.py` 中配置 vLLM 服务：

```python
# vLLM配置
VLLM_BASE_URL: str = "http://221.226.33.59:8000"  # 您的vLLM服务地址
VLLM_TIMEOUT: int = 30
VLLM_DEFAULT_MODEL: str = "default"
```

### 2. MCP 协议配置

```python
# MCP协议配置
MCP_ENABLED: bool = True
MCP_SERVER_NAME: str = "Model Control MCP Server"
MCP_SERVER_VERSION: str = "1.0.0"
```

### 3. 环境变量配置（推荐）

在项目根目录创建 `.env` 文件：

```bash
# Model Control AI System 配置
PROJECT_NAME=Model Control AI System

# 数据库配置
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=root
MONGO_PASSWORD=your_password_here
MONGO_AUTH_SOURCE=admin

# 数据库名称
MONGO_DB_NAME=control_db
DJI_DB_NAME=dji
CONTROL_DB_NAME=control_db
MAVLINK_MONGO_DB_NAME=control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=ai_control_analytics

# vLLM服务配置（更新为您的实际端口）
VLLM_BASE_URL=http://221.226.33.59:2800
VLLM_TIMEOUT=30
VLLM_DEFAULT_MODEL=default

# MCP协议配置
MCP_ENABLED=true
MCP_SERVER_NAME=Model Control MCP Server
MCP_SERVER_VERSION=1.0.0
```

**注意**: 可以将 `env.example` 复制为 `.env` 然后修改您的具体配置。

## API 接口

### 1. LLM 相关接口

#### 健康检查
```http
GET /api/v1/llm/health
```

#### 获取可用模型
```http
GET /api/v1/llm/models
```

#### 聊天完成
```http
POST /api/v1/llm/chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "你好"}
  ],
  "model": "default",
  "temperature": 0.7,
  "max_tokens": 2048,
  "stream": false
}
```

#### 流式聊天
```http
POST /api/v1/llm/chat/completions
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "请详细解释人工智能"}
  ],
  "stream": true
}
```

#### 文本完成
```http
POST /api/v1/llm/completions?prompt=人工智能的未来是&temperature=0.7
```

#### 增强聊天（集成 MCP）
```http
POST /api/v1/llm/chat/enhanced
Content-Type: application/json

{
  "messages": [
    {"role": "user", "content": "获取系统状态"}
  ],
  "use_mcp_tools": true,
  "use_mcp_prompts": false
}
```

#### 系统状态
```http
GET /api/v1/llm/status
```

### 2. MCP 协议接口

#### 列出资源
```http
GET /api/v1/mcp/resources
```

#### 列出工具
```http
GET /api/v1/mcp/tools
```

#### 调用工具
```http
POST /api/v1/mcp/tools/{tool_name}/call
Content-Type: application/json

{
  "arg1": "value1",
  "arg2": "value2"
}
```

#### 列出提示模板
```http
GET /api/v1/mcp/prompts
```

#### 获取提示模板
```http
POST /api/v1/mcp/prompts/{prompt_name}
Content-Type: application/json

{
  "arguments": {
    "param1": "value1"
  }
}
```

#### 处理原始 MCP 消息
```http
POST /api/v1/mcp/message
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "ping",
  "id": 1
}
```

## Python 客户端使用示例

### 基本用法

```python
import httpx
import asyncio

async def chat_example():
    async with httpx.AsyncClient() as client:
        # 聊天完成
        response = await client.post(
            "http://localhost:2000/api/v1/llm/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "你好，请介绍一下你自己"}
                ]
            }
        )
        data = response.json()
        print(data["choices"][0]["message"]["content"])

asyncio.run(chat_example())
```

### 流式聊天

```python
import httpx
import json

async def stream_chat():
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://localhost:2000/api/v1/llm/chat/completions",
            json={
                "messages": [
                    {"role": "user", "content": "请详细解释人工智能"}
                ],
                "stream": True
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if "choices" in data:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                print(delta["content"], end="")
                    except json.JSONDecodeError:
                        continue

asyncio.run(stream_chat())
```

### 使用提供的客户端类

```python
# 使用 examples/llm_example.py 中的 LLMClient 类
from examples.llm_example import LLMClient

async def main():
    async with LLMClient() as client:
        # 检查健康状态
        health = await client.check_health()
        print(f"健康状态: {health}")
        
        # 聊天
        response = await client.chat_completion([
            {"role": "user", "content": "你好"}
        ])
        print(response)
        
        # 增强聊天
        enhanced = await client.enhanced_chat([
            {"role": "user", "content": "获取系统信息"}
        ], use_mcp_tools=True)
        print(enhanced)

asyncio.run(main())
```

## 运行示例

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

```bash
python start_server.py
# 或
python -m uvicorn src.app.main:app --host 0.0.0.0 --port 2000 --reload
```

### 3. 运行示例

```bash
# 运行基本示例
python examples/llm_example.py

# 运行交互式聊天
python examples/llm_example.py interactive
```

### 4. 访问 API 文档

打开浏览器访问：
- Swagger UI: http://localhost:2000/docs
- ReDoc: http://localhost:2000/redoc

## 故障排除

### 1. vLLM 服务连接失败

确保 vLLM 服务正在运行并且可以访问：

```bash
curl http://221.226.33.59:8000/health
```

### 2. 检查配置

确认 `src/app/config.py` 中的 `VLLM_BASE_URL` 配置正确。

### 3. 查看日志

服务启动时会显示详细的状态信息，包括 vLLM 服务的连接状态。

### 4. 测试连接

```bash
# 测试基本连接
curl http://localhost:2000/api/v1/llm/health

# 测试模型列表
curl http://localhost:2000/api/v1/llm/models

# 测试系统状态
curl http://localhost:2000/api/v1/llm/status
```

## MCP 协议扩展

### 添加自定义资源

```python
from app.mcp.protocol import MCPResource, get_mcp_server

# 注册自定义资源
server = get_mcp_server()
server.register_resource(MCPResource(
    uri="custom://my-resource",
    name="My Custom Resource",
    description="A custom resource for demonstration",
    mimeType="application/json"
))
```

### 添加自定义工具

```python
from app.mcp.protocol import MCPTool, get_mcp_server

# 注册自定义工具
server = get_mcp_server()
server.register_tool(MCPTool(
    name="my_tool",
    description="A custom tool",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string"},
            "param2": {"type": "number"}
        }
    }
))

# 注册工具处理器
async def handle_my_tool(params):
    # 处理工具调用逻辑
    return {"result": "Tool executed successfully"}

server.register_handler("tools/my_tool", handle_my_tool)
```

## 性能优化

### 1. 连接池

vLLM 客户端使用 httpx 的连接池，支持并发请求。

### 2. 异步处理

所有 API 接口都是异步的，支持高并发处理。

### 3. 流式响应

对于长文本生成，建议使用流式响应以提供更好的用户体验。

## 安全注意事项

1. 在生产环境中，确保 vLLM 服务的网络安全
2. 考虑添加 API 认证和授权
3. 监控和限制 API 调用频率
4. 验证用户输入，防止注入攻击

## 更多信息

- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [vLLM 文档](https://docs.vllm.ai/)
- [MCP 协议规范](https://modelcontextprotocol.io/)

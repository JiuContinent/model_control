"""
vLLM和MCP协议使用示例
演示如何调用集成的LLM服务
"""
import asyncio
import httpx
import json
from typing import List, Dict, Any


class LLMClient:
    """LLM API客户端示例"""
    
    def __init__(self, base_url: str = "http://localhost:2000"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient()
    
    async def close(self):
        await self.client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def check_health(self) -> Dict[str, Any]:
        """检查LLM服务健康状态"""
        response = await self.client.get(f"{self.base_url}/api/v1/llm/health")
        response.raise_for_status()
        return response.json()
    
    async def list_models(self) -> Dict[str, Any]:
        """获取可用模型列表"""
        response = await self.client.get(f"{self.base_url}/api/v1/llm/models")
        response.raise_for_status()
        return response.json()
    
    async def chat_completion(self, messages: List[Dict[str, str]], 
                            model: str = None, stream: bool = False) -> Dict[str, Any]:
        """聊天完成"""
        payload = {
            "messages": messages,
            "model": model,
            "temperature": 0.7,
            "max_tokens": 2048,
            "stream": stream
        }
        
        if stream:
            return await self._stream_chat(payload)
        else:
            response = await self.client.post(
                f"{self.base_url}/api/v1/llm/chat/completions",
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def _stream_chat(self, payload: Dict[str, Any]):
        """流式聊天"""
        async with self.client.stream(
            "POST",
            f"{self.base_url}/api/v1/llm/chat/completions",
            json=payload
        ) as response:
            response.raise_for_status()
            
            content = ""
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    
                    try:
                        data = json.loads(data_str)
                        if "choices" in data and data["choices"]:
                            delta = data["choices"][0].get("delta", {})
                            if "content" in delta:
                                content += delta["content"]
                                print(delta["content"], end="", flush=True)
                    except json.JSONDecodeError:
                        continue
            
            return {"content": content}
    
    async def text_completion(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """文本完成"""
        params = {
            "prompt": prompt,
            "model": model,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/llm/completions",
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    async def enhanced_chat(self, messages: List[Dict[str, str]], 
                          use_mcp_tools: bool = False, 
                          use_mcp_prompts: bool = False) -> Dict[str, Any]:
        """增强聊天（集成MCP协议）"""
        payload = {
            "messages": messages,
            "use_mcp_tools": use_mcp_tools,
            "use_mcp_prompts": use_mcp_prompts
        }
        
        response = await self.client.post(
            f"{self.base_url}/api/v1/llm/chat/enhanced",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    async def get_status(self) -> Dict[str, Any]:
        """获取LLM系统状态"""
        response = await self.client.get(f"{self.base_url}/api/v1/llm/status")
        response.raise_for_status()
        return response.json()
    
    # MCP协议相关方法
    async def list_mcp_resources(self) -> Dict[str, Any]:
        """列出MCP资源"""
        response = await self.client.get(f"{self.base_url}/api/v1/mcp/resources")
        response.raise_for_status()
        return response.json()
    
    async def list_mcp_tools(self) -> Dict[str, Any]:
        """列出MCP工具"""
        response = await self.client.get(f"{self.base_url}/api/v1/mcp/tools")
        response.raise_for_status()
        return response.json()
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/mcp/tools/{tool_name}/call",
            json=arguments
        )
        response.raise_for_status()
        return response.json()


async def main():
    """主函数，演示各种功能"""
    print("=== vLLM 和 MCP 协议集成示例 ===\n")
    
    async with LLMClient() as client:
        try:
            # 1. 检查健康状态
            print("1. 检查LLM服务健康状态...")
            health = await client.check_health()
            print(f"健康状态: {health}\n")
            
            # 2. 获取系统状态
            print("2. 获取系统状态...")
            status = await client.get_status()
            print(f"系统状态: {status}\n")
            
            # 3. 列出可用模型
            print("3. 获取可用模型...")
            models = await client.list_models()
            print(f"可用模型: {models}\n")
            
            # 4. 简单聊天
            print("4. 简单聊天示例...")
            messages = [
                {"role": "user", "content": "你好，请介绍一下你自己"}
            ]
            
            response = await client.chat_completion(messages)
            print(f"聊天响应: {response}\n")
            
            # 5. 流式聊天
            print("5. 流式聊天示例...")
            print("问题: 请解释什么是人工智能？")
            print("回答: ", end="")
            
            stream_messages = [
                {"role": "user", "content": "请解释什么是人工智能？"}
            ]
            
            await client.chat_completion(stream_messages, stream=True)
            print("\n")
            
            # 6. 文本完成
            print("6. 文本完成示例...")
            completion = await client.text_completion("人工智能的未来发展趋势是")
            print(f"文本完成: {completion}\n")
            
            # 7. MCP协议相关功能
            print("7. MCP协议功能演示...")
            
            # 列出MCP资源
            print("  - 列出MCP资源...")
            resources = await client.list_mcp_resources()
            print(f"  MCP资源: {resources}")
            
            # 列出MCP工具
            print("  - 列出MCP工具...")
            tools = await client.list_mcp_tools()
            print(f"  MCP工具: {tools}")
            
            # 8. 增强聊天（集成MCP）
            print("8. 增强聊天示例（集成MCP协议）...")
            enhanced_response = await client.enhanced_chat(
                messages=[
                    {"role": "user", "content": "使用系统工具获取当前状态"}
                ],
                use_mcp_tools=True
            )
            print(f"增强聊天响应: {enhanced_response}\n")
            
        except Exception as e:
            print(f"错误: {e}")


async def interactive_chat():
    """交互式聊天示例"""
    print("=== 交互式聊天模式 ===")
    print("输入 'quit' 退出, 'stream' 切换流式模式, 'enhanced' 使用增强模式")
    
    async with LLMClient() as client:
        messages = []
        stream_mode = False
        enhanced_mode = False
        
        while True:
            user_input = input("\n你: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'stream':
                stream_mode = not stream_mode
                print(f"流式模式: {'开启' if stream_mode else '关闭'}")
                continue
            elif user_input.lower() == 'enhanced':
                enhanced_mode = not enhanced_mode
                print(f"增强模式: {'开启' if enhanced_mode else '关闭'}")
                continue
            elif user_input.lower() == 'clear':
                messages = []
                print("对话历史已清空")
                continue
            
            if not user_input:
                continue
            
            messages.append({"role": "user", "content": user_input})
            
            try:
                print("AI: ", end="")
                
                if enhanced_mode:
                    response = await client.enhanced_chat(
                        messages=messages,
                        use_mcp_tools=True
                    )
                    content = response.get("content", "")
                    print(content)
                elif stream_mode:
                    result = await client.chat_completion(messages, stream=True)
                    content = result.get("content", "")
                else:
                    response = await client.chat_completion(messages)
                    content = response["choices"][0]["message"]["content"]
                    print(content)
                
                messages.append({"role": "assistant", "content": content})
                
            except Exception as e:
                print(f"错误: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_chat())
    else:
        asyncio.run(main())

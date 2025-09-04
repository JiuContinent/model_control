"""
vLLM和MCP集成测试
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from app.llm.vllm_client import vLLMClient, ChatMessage, ChatRequest
from app.mcp.protocol import MCPServer, MCPMessage, MCPResource, MCPTool


class TestvLLMClient:
    """vLLM客户端测试"""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """测试健康检查"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_client.return_value.get = AsyncMock(return_value=mock_response)
            
            client = vLLMClient("http://test:8000")
            result = await client.health_check()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_list_models(self):
        """测试获取模型列表"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_response.json.return_value = {
                "data": [
                    {"id": "model1", "object": "model"},
                    {"id": "model2", "object": "model"}
                ]
            }
            mock_client.return_value.get = AsyncMock(return_value=mock_response)
            
            client = vLLMClient("http://test:8000")
            models = await client.list_models()
            
            assert len(models) == 2
            assert models[0]["id"] == "model1"
    
    @pytest.mark.asyncio
    async def test_chat_completion(self):
        """测试聊天完成"""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = AsyncMock()
            mock_response.json.return_value = {
                "choices": [
                    {
                        "message": {
                            "content": "Hello! How can I help you?"
                        }
                    }
                ],
                "model": "test-model",
                "usage": {"total_tokens": 10}
            }
            mock_client.return_value.post = AsyncMock(return_value=mock_response)
            
            client = vLLMClient("http://test:8000")
            request = ChatRequest(
                messages=[ChatMessage(role="user", content="Hello")]
            )
            
            response = await client.chat_completion(request)
            
            assert response.content == "Hello! How can I help you?"
            assert response.model == "test-model"


class TestMCPServer:
    """MCP服务器测试"""
    
    def test_register_resource(self):
        """测试注册资源"""
        server = MCPServer()
        resource = MCPResource(
            uri="test://resource",
            name="Test Resource",
            description="A test resource"
        )
        
        server.register_resource(resource)
        
        assert "test://resource" in server.resources
        assert server.resources["test://resource"].name == "Test Resource"
    
    def test_register_tool(self):
        """测试注册工具"""
        server = MCPServer()
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            inputSchema={"type": "object"}
        )
        
        server.register_tool(tool)
        
        assert "test_tool" in server.tools
        assert server.tools["test_tool"].description == "A test tool"
    
    @pytest.mark.asyncio
    async def test_handle_ping(self):
        """测试ping处理"""
        server = MCPServer()
        message = MCPMessage(method="ping", id=1)
        
        response = await server.handle_message(message)
        
        assert response.id == 1
        assert response.error is None
        assert response.result == {}
    
    @pytest.mark.asyncio
    async def test_handle_initialize(self):
        """测试初始化处理"""
        server = MCPServer()
        message = MCPMessage(
            method="initialize",
            id=1,
            params={
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "test-client"}
            }
        )
        
        response = await server.handle_message(message)
        
        assert response.id == 1
        assert response.error is None
        assert "serverInfo" in response.result
        assert "capabilities" in response.result
    
    @pytest.mark.asyncio
    async def test_handle_list_resources(self):
        """测试列出资源"""
        server = MCPServer()
        
        # 添加测试资源
        resource = MCPResource(
            uri="test://resource",
            name="Test Resource"
        )
        server.register_resource(resource)
        
        message = MCPMessage(method="resources/list", id=1)
        response = await server.handle_message(message)
        
        assert response.id == 1
        assert response.error is None
        assert "resources" in response.result
        assert len(response.result["resources"]) == 1
        assert response.result["resources"][0]["uri"] == "test://resource"


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_vllm_mcp_integration(self):
        """测试vLLM和MCP的集成"""
        # 这里可以添加端到端的集成测试
        # 例如：启动服务器，发送请求，验证响应
        pass
    
    def test_config_loading(self):
        """测试配置加载"""
        from app.config import settings
        
        # 验证vLLM配置
        assert hasattr(settings, 'VLLM_BASE_URL')
        assert hasattr(settings, 'VLLM_TIMEOUT')
        assert hasattr(settings, 'VLLM_DEFAULT_MODEL')
        
        # 验证MCP配置
        assert hasattr(settings, 'MCP_ENABLED')
        assert hasattr(settings, 'MCP_SERVER_NAME')
        assert hasattr(settings, 'MCP_SERVER_VERSION')


if __name__ == "__main__":
    # 运行简单的测试
    async def run_basic_tests():
        print("运行基本功能测试...")
        
        # 测试vLLM客户端创建
        client = vLLMClient("http://test:8000")
        print("✓ vLLM客户端创建成功")
        
        # 测试MCP服务器创建
        server = MCPServer()
        print("✓ MCP服务器创建成功")
        
        # 测试资源注册
        resource = MCPResource(
            uri="test://resource",
            name="Test Resource"
        )
        server.register_resource(resource)
        print("✓ MCP资源注册成功")
        
        # 测试工具注册
        tool = MCPTool(
            name="test_tool",
            description="Test tool",
            inputSchema={"type": "object"}
        )
        server.register_tool(tool)
        print("✓ MCP工具注册成功")
        
        print("所有基本测试通过！")
    
    asyncio.run(run_basic_tests())

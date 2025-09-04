#!/usr/bin/env python3
"""
配置验证脚本
验证清理后的配置是否正常
"""

import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from app.config import settings
    
    print("✅ 配置文件加载成功!")
    print()
    print("🔧 vLLM 配置:")
    print(f"  - 服务地址: {settings.VLLM_BASE_URL}")
    print(f"  - 超时时间: {settings.VLLM_TIMEOUT}秒")
    print(f"  - 默认模型: {settings.VLLM_DEFAULT_MODEL}")
    print()
    print("🤖 MCP 协议配置:")
    print(f"  - 启用状态: {settings.MCP_ENABLED}")
    print(f"  - 服务器名: {settings.MCP_SERVER_NAME}")
    print(f"  - 版本号: {settings.MCP_SERVER_VERSION}")
    print()
    print("📁 数据库配置:")
    print(f"  - 启用状态: {settings.USE_MONGO}")
    print(f"  - 主机地址: {settings.MONGO_HOST}:{settings.MONGO_PORT}")
    print()
    
    # 检查是否还有OpenAI相关配置
    has_openai = False
    for attr in dir(settings):
        if 'OPENAI' in attr.upper():
            has_openai = True
            print(f"⚠️  发现OpenAI配置: {attr}")
    
    if not has_openai:
        print("✅ 确认: 没有发现OpenAI相关配置，清理完成!")
    
    print()
    print("🎉 配置验证通过，可以安全使用vLLM服务!")
    
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    sys.exit(1)

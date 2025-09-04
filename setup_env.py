#!/usr/bin/env python3
"""
快速设置环境配置文件的脚本
"""
import os
from pathlib import Path

def create_env_file():
    """创建.env配置文件"""
    
    env_content = """# Model Control AI System 配置文件
# 自动生成于 setup_env.py

# ==================== 项目基本配置 ====================
PROJECT_NAME=Model Control AI System

# ==================== 数据库配置 ====================
USE_MONGO=true

# MongoDB服务器配置
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=root
MONGO_PASSWORD=RedFlym3o6n9@&#
MONGO_AUTH_SOURCE=admin

# 数据库名称配置
MONGO_DB_NAME=control_db
DJI_DB_NAME=dji
CONTROL_DB_NAME=control_db

# 多数据源配置
MAVLINK_MONGO_DB_NAME=control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=ai_control_analytics

# ==================== vLLM服务配置 ====================
# vLLM服务地址（您的Docker服务地址，端口2800）
VLLM_BASE_URL=http://221.226.33.59:2800
VLLM_TIMEOUT=30
VLLM_DEFAULT_MODEL=default

# ==================== MCP协议配置 ====================
MCP_ENABLED=true
MCP_SERVER_NAME=Model Control MCP Server
MCP_SERVER_VERSION=1.0.0

# ==================== MQTT配置 ====================
# MQTT broker配置
MQTT_HOST=221.226.33.58
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
MQTT_TOPIC=/ue/device/mavlink

# ==================== 服务器配置 ====================
# FastAPI服务器配置
SERVER_HOST=0.0.0.0
SERVER_PORT=2000
SERVER_RELOAD=true

# ==================== 日志配置 ====================
# 日志级别 (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/app.log
LOG_ROTATION=50 MB
LOG_RETENTION=30 days

# ==================== 其他配置 ====================
# 调试模式
DEBUG=false
"""

    env_file = Path('.env')
    
    if env_file.exists():
        backup_file = Path('.env.backup')
        print(f"⚠️  发现现有的 .env 文件，备份为 {backup_file}")
        env_file.rename(backup_file)
    
    env_file.write_text(env_content.strip(), encoding='utf-8')
    print(f"✅ 已创建 .env 配置文件")
    return env_file


def validate_config():
    """验证配置是否正确加载"""
    try:
        import sys
        sys.path.append('src')
        
        from app.config import settings
        
        print("\n🔧 配置验证结果:")
        print(f"  📋 项目名称: {settings.PROJECT_NAME}")
        print(f"  🤖 vLLM服务: {settings.VLLM_BASE_URL}")
        print(f"  ⏱️  vLLM超时: {settings.VLLM_TIMEOUT}s")
        print(f"  🔗 MCP启用: {settings.MCP_ENABLED}")
        print(f"  🗄️  MongoDB: {settings.MONGO_HOST}:{settings.MONGO_PORT}")
        print(f"  📡 MQTT: {settings.MONGO_HOST}:1883")
        
        print("\n✅ 配置加载成功!")
        return True
        
    except Exception as e:
        print(f"\n❌ 配置验证失败: {e}")
        return False


def test_vllm_connection():
    """测试vLLM服务连接"""
    try:
        import requests
        import time
        
        print("\n🔗 测试vLLM服务连接...")
        
        start_time = time.time()
        response = requests.get('http://221.226.33.59:2800/health', timeout=10)
        duration = time.time() - start_time
        
        print(f"✅ vLLM服务连接成功!")
        print(f"   📊 状态码: {response.status_code}")
        print(f"   ⏱️  响应时间: {duration:.2f}s")
        
        if response.status_code == 200:
            print("   🎉 vLLM服务健康状态良好!")
        else:
            print(f"   ⚠️  vLLM服务状态异常: {response.text[:100]}")
            
        return True
        
    except requests.exceptions.ConnectException:
        print("❌ 无法连接到vLLM服务 (221.226.33.59:2800)")
        print("   请检查:")
        print("   1. vLLM Docker容器是否正在运行")
        print("   2. 端口2800是否正确")
        print("   3. 防火墙设置")
        return False
        
    except Exception as e:
        print(f"❌ vLLM连接测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🚀 Model Control AI System 环境配置向导")
    print("=" * 50)
    
    # 1. 创建.env文件
    print("\n📝 步骤 1: 创建环境配置文件")
    env_file = create_env_file()
    
    # 2. 验证配置
    print("\n📝 步骤 2: 验证配置加载")
    config_ok = validate_config()
    
    # 3. 测试vLLM连接
    print("\n📝 步骤 3: 测试vLLM服务连接")
    vllm_ok = test_vllm_connection()
    
    # 总结
    print("\n" + "=" * 50)
    print("🎯 配置完成总结:")
    print(f"   📁 环境文件: {env_file.absolute()}")
    print(f"   ⚙️  配置加载: {'✅ 成功' if config_ok else '❌ 失败'}")
    print(f"   🤖 vLLM连接: {'✅ 成功' if vllm_ok else '❌ 失败'}")
    
    if config_ok and vllm_ok:
        print("\n🎉 所有配置都正常! 可以启动服务了:")
        print("   python start_server.py")
    else:
        print("\n⚠️  存在配置问题，请检查上述错误信息")
    
    print("\n💡 提示:")
    print("   - 可以手动编辑 .env 文件来修改配置")
    print("   - 配置文件支持项目根目录和 src/app/ 目录")
    print("   - 重启服务后配置会自动生效")


if __name__ == "__main__":
    main()



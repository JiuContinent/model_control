#!/usr/bin/env python3
"""
启动实时AI识别服务器

端口: 2000
自动检测GPU配置
"""

import uvicorn
import sys
from pathlib import Path

# 添加src到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    print("🚀 启动实时AI识别服务器...")
    print("📍 服务地址: http://localhost:2000")
    print("📖 API文档: http://localhost:2000/docs")
    print("🔧 系统信息: http://localhost:2000/api/v1/realtime-ai/gpu-info")
    print("=" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=2000,
        reload=True,
        log_level="info",
        app_dir="src"
    )

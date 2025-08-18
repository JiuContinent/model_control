#!/usr/bin/env python3
"""
Model Control AI System 启动脚本
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 11):
        print("? 错误: 需要Python 3.11或更高版本")
        print(f"当前版本: {sys.version}")
        sys.exit(1)
    print(f"? Python版本检查通过: {sys.version}")


def create_directories():
    """创建必要的目录"""
    directories = [
        "logs",
        "uploads", 
        "models",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"? 创建目录: {directory}")


def install_dependencies():
    """安装依赖"""
    print("? 安装项目依赖...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("? 依赖安装完成")
    except subprocess.CalledProcessError as e:
        print(f"? 依赖安装失败: {e}")
        sys.exit(1)


def create_env_file():
    """创建环境配置文件"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# MongoDB 配置
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=model_control

# AI 模型配置
AI_MODEL_PATH=models/yolov11.pt
AI_CONFIDENCE_THRESHOLD=0.5
AI_IOU_THRESHOLD=0.45

# MAVLink 配置
MAVLINK_HOST=0.0.0.0
MAVLINK_PORT=5760

# 日志配置
LOG_LEVEL=INFO

# 项目配置
PROJECT_NAME=Model Control AI System
DEBUG=true
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("? 创建环境配置文件: .env")
    else:
        print("??  环境配置文件已存在: .env")


def download_yolo_model():
    """下载YOLOv11模型"""
    models_dir = Path("models")
    model_path = models_dir / "yolov11n.pt"
    
    if not model_path.exists():
        print("? 下载YOLOv11模型...")
        try:
            from ultralytics import YOLO
            # 下载nano版本的YOLOv11
            model = YOLO("yolov11n.pt")
            print("? YOLOv11模型下载完成")
        except Exception as e:
            print(f"??  模型下载失败: {e}")
            print("??  首次运行时会自动下载模型")
    else:
        print("? YOLOv11模型已存在")


def start_application():
    """启动应用"""
    print("? 启动Model Control AI System...")
    print("? API文档: http://localhost:8000/docs")
    print("? 健康检查: http://localhost:8000/health")
    print("??  按Ctrl+C停止服务")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000", 
            "--reload",
            "--app-dir", "src"
        ])
    except KeyboardInterrupt:
        print("\n? 服务已停止")
    except Exception as e:
        print(f"? 启动失败: {e}")


def main():
    """主函数"""
    print("=" * 50)
    print("? Model Control AI System 启动器")
    print("=" * 50)
    
    # 检查Python版本
    check_python_version()
    
    # 创建目录
    create_directories()
    
    # 创建环境配置
    create_env_file()
    
    # 安装依赖
    install_dependencies()
    
    # 下载模型
    download_yolo_model()
    
    # 启动应用
    start_application()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Model Control AI System Startup Script
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version"""
    if sys.version_info < (3, 11):
        print("? Error: Python 3.11 or higher required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"? Python version check passed: {sys.version}")


def create_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "uploads", 
        "models",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"? Created directory: {directory}")


def install_dependencies():
    """Install dependencies"""
    print("? Installing project dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("? Dependencies installation completed")
    except subprocess.CalledProcessError as e:
        print(f"? Dependencies installation failed: {e}")
        sys.exit(1)


def create_env_file():
    """Create environment configuration file"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# MongoDB Configuration - 支持认证
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=
MONGO_PASSWORD=
MONGO_AUTH_SOURCE=admin
USE_MONGO=true

# 主要数据库配置
MONGO_DB_NAME=control_db
CONTROL_DB_NAME=control_db
DJI_DB_NAME=dji

# 专用数据源配置
MAVLINK_MONGO_DB_NAME=control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=ai_control_analytics

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1

# AI Model Configuration
AI_MODEL_PATH=models/yolov11.pt
AI_CONFIDENCE_THRESHOLD=0.5
AI_IOU_THRESHOLD=0.45

# MAVLink Configuration
MAVLINK_HOST=0.0.0.0
MAVLINK_PORT=5760

# Logging Configuration
LOG_LEVEL=INFO

# Project Configuration
PROJECT_NAME=Model Control AI System
DEBUG=true
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("? Created environment configuration file: .env")
    else:
        print("??  Environment configuration file already exists: .env")


def download_yolo_model():
    """Download YOLOv11 model"""
    models_dir = Path("models")
    model_path = models_dir / "yolov11n.pt"
    
    if not model_path.exists():
        print("? Downloading YOLOv11 model...")
        try:
            from ultralytics import YOLO
            # Download nano version of YOLOv11
            model = YOLO("yolov11n.pt")
            print("? YOLOv11 model download completed")
        except Exception as e:
            print(f"??  Model download failed: {e}")
            print("??  Model will be automatically downloaded on first run")
    else:
        print("? YOLOv11 model already exists")


def start_application():
    """Start application"""
    print("? Starting Model Control AI System...")
    print("? API Documentation: http://localhost:8000/docs")
    print("? Health Check: http://localhost:8000/health")
    print("??  Press Ctrl+C to stop service")
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
        print("\n? Service stopped")
    except Exception as e:
        print(f"? Startup failed: {e}")


def main():
    """Main function"""
    print("=" * 50)
    print("? Model Control AI System Launcher")
    print("=" * 50)
    
    # Check Python version
    check_python_version()
    
    # Create directories
    create_directories()
    
    # Create environment configuration
    create_env_file()
    
    # Install dependencies
    install_dependencies()
    
    # Download model
    download_yolo_model()
    
    # Start application
    start_application()


if __name__ == "__main__":
    main()

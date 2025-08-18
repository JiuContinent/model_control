#!/usr/bin/env python3
"""
Model Control AI System �����ű�
"""
import os
import sys
import subprocess
from pathlib import Path


def check_python_version():
    """���Python�汾"""
    if sys.version_info < (3, 11):
        print("? ����: ��ҪPython 3.11����߰汾")
        print(f"��ǰ�汾: {sys.version}")
        sys.exit(1)
    print(f"? Python�汾���ͨ��: {sys.version}")


def create_directories():
    """������Ҫ��Ŀ¼"""
    directories = [
        "logs",
        "uploads", 
        "models",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"? ����Ŀ¼: {directory}")


def install_dependencies():
    """��װ����"""
    print("? ��װ��Ŀ����...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], check=True)
        print("? ������װ���")
    except subprocess.CalledProcessError as e:
        print(f"? ������װʧ��: {e}")
        sys.exit(1)


def create_env_file():
    """�������������ļ�"""
    env_file = Path(".env")
    if not env_file.exists():
        env_content = """# MongoDB ����
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=model_control

# AI ģ������
AI_MODEL_PATH=models/yolov11.pt
AI_CONFIDENCE_THRESHOLD=0.5
AI_IOU_THRESHOLD=0.45

# MAVLink ����
MAVLINK_HOST=0.0.0.0
MAVLINK_PORT=5760

# ��־����
LOG_LEVEL=INFO

# ��Ŀ����
PROJECT_NAME=Model Control AI System
DEBUG=true
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        print("? �������������ļ�: .env")
    else:
        print("??  ���������ļ��Ѵ���: .env")


def download_yolo_model():
    """����YOLOv11ģ��"""
    models_dir = Path("models")
    model_path = models_dir / "yolov11n.pt"
    
    if not model_path.exists():
        print("? ����YOLOv11ģ��...")
        try:
            from ultralytics import YOLO
            # ����nano�汾��YOLOv11
            model = YOLO("yolov11n.pt")
            print("? YOLOv11ģ���������")
        except Exception as e:
            print(f"??  ģ������ʧ��: {e}")
            print("??  �״�����ʱ���Զ�����ģ��")
    else:
        print("? YOLOv11ģ���Ѵ���")


def start_application():
    """����Ӧ��"""
    print("? ����Model Control AI System...")
    print("? API�ĵ�: http://localhost:8000/docs")
    print("? �������: http://localhost:8000/health")
    print("??  ��Ctrl+Cֹͣ����")
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
        print("\n? ������ֹͣ")
    except Exception as e:
        print(f"? ����ʧ��: {e}")


def main():
    """������"""
    print("=" * 50)
    print("? Model Control AI System ������")
    print("=" * 50)
    
    # ���Python�汾
    check_python_version()
    
    # ����Ŀ¼
    create_directories()
    
    # ������������
    create_env_file()
    
    # ��װ����
    install_dependencies()
    
    # ����ģ��
    download_yolo_model()
    
    # ����Ӧ��
    start_application()


if __name__ == "__main__":
    main()

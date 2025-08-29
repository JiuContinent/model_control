"""
简单的API测试文件，用于隔离Pydantic问题
"""

from typing import Optional, List
from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime

# 简化的枚举类型
from app.realtime_ai.core.base import DetectorType, StreamProtocol

router = APIRouter(prefix="/test", tags=["Test"])

# 最简单的模型定义
class SimpleStreamConfig(BaseModel):
    url: str
    protocol: Optional[str] = None

class SimpleModelConfig(BaseModel):
    variant: str = "yolov11n"
    device: str = "auto"
    enable_multi_gpu: bool = False

class SimpleRequest(BaseModel):
    stream_config: SimpleStreamConfig
    model_config: Optional[SimpleModelConfig] = None

@router.get("/health")
async def test_health():
    """简单的健康检查"""
    return {"status": "ok", "timestamp": datetime.now()}

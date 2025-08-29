"""
Real-time AI Recognition Module

A modern, extensible real-time AI recognition system supporting multiple
streaming protocols (RTSP/RTMP) and various AI detection models.

Architecture:
- Abstract base classes for extensibility
- Factory pattern for detector creation
- Strategy pattern for different AI algorithms
- Async/await for high performance
- Plugin-based detector system
"""

from .core.base import BaseRealtimeDetector, BaseStreamProvider, DetectorType, StreamProtocol, StreamConfig
from .core.factory import DetectorFactory, StreamProviderFactory
from .detectors.yolo_detector import YOLOv11Detector
from .detectors.custom_detector import CustomDetector
from .detectors.multi_gpu_detector import MultiGPUYOLOv11Detector
from .streams.rtsp_provider import RTSPStreamProvider
from .streams.rtmp_provider import RTMPStreamProvider
from .streams.http_provider import HTTPStreamProvider
from .streams.file_provider import FileStreamProvider
from .service import RealtimeAIService, ServiceConfig, create_rtsp_yolo_service, create_rtmp_yolo_service

# Import registry to auto-register all components
from . import registry

__all__ = [
    "BaseRealtimeDetector",
    "BaseStreamProvider", 
    "DetectorType",
    "StreamProtocol",
    "StreamConfig",
    "DetectorFactory",
    "StreamProviderFactory",
    "YOLOv11Detector",
    "CustomDetector",
    "MultiGPUYOLOv11Detector",
    "RTSPStreamProvider",
    "RTMPStreamProvider",
    "HTTPStreamProvider",
    "FileStreamProvider",
    "RealtimeAIService",
    "ServiceConfig",
    "create_rtsp_yolo_service",
    "create_rtmp_yolo_service",
]

__version__ = "1.0.0"
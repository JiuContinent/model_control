"""
AI Detectors for real-time recognition.

Provides different YOLO variants and custom detector implementations.
"""

from .yolo_detector import YOLOv11Detector
from .custom_detector import CustomDetector
from .multi_gpu_detector import MultiGPUYOLOv11Detector
from .vehicle_detector import VehicleDetector, MultiVehicleTypeDetector

__all__ = [
    "YOLOv11Detector",
    "CustomDetector",
    "MultiGPUYOLOv11Detector",
    "VehicleDetector",
    "MultiVehicleTypeDetector",
]

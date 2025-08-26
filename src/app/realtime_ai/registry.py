"""
Registry for detectors and stream providers.

Automatically registers all available detectors and stream providers
with their respective factories.
"""

from .core.factory import DetectorFactory, StreamProviderFactory
from .core.base import DetectorType, StreamProtocol

# Import all detectors
from .detectors.yolo_detector import YOLOv11Detector
from .detectors.custom_detector import CustomDetector
from .detectors.multi_gpu_detector import MultiGPUYOLOv11Detector
from .detectors.vehicle_detector import VehicleDetector, MultiVehicleTypeDetector

# Import all stream providers  
from .streams.rtsp_provider import RTSPStreamProvider
from .streams.rtmp_provider import RTMPStreamProvider
from .streams.http_provider import HTTPStreamProvider
from .streams.file_provider import FileStreamProvider


def register_all():
    """Register all available detectors and stream providers"""
    
    # Register YOLO detectors for all variants
    for detector_type in [
        DetectorType.YOLOV11_NANO,
        DetectorType.YOLOV11_SMALL,
        DetectorType.YOLOV11_MEDIUM,
        DetectorType.YOLOV11_LARGE,
        DetectorType.YOLOV11_XLARGE
    ]:
        DetectorFactory.register(detector_type, YOLOv11Detector)
    
    # Register multi-GPU detectors
    for detector_type in [
        DetectorType.MULTI_GPU_YOLOV11_NANO,
        DetectorType.MULTI_GPU_YOLOV11_SMALL,
        DetectorType.MULTI_GPU_YOLOV11_MEDIUM,
        DetectorType.MULTI_GPU_YOLOV11_LARGE,
        DetectorType.MULTI_GPU_YOLOV11_XLARGE
    ]:
        DetectorFactory.register(detector_type, MultiGPUYOLOv11Detector)
    
    # Register vehicle detectors
    DetectorFactory.register(DetectorType.VEHICLE_DETECTOR, VehicleDetector)
    DetectorFactory.register(DetectorType.MULTI_VEHICLE_TYPE, MultiVehicleTypeDetector)
    
    # Register custom detector
    DetectorFactory.register(DetectorType.CUSTOM, CustomDetector)
    
    # Register stream providers
    StreamProviderFactory.register(StreamProtocol.RTSP, RTSPStreamProvider)
    StreamProviderFactory.register(StreamProtocol.RTMP, RTMPStreamProvider)
    StreamProviderFactory.register(StreamProtocol.HTTP, HTTPStreamProvider)
    StreamProviderFactory.register(StreamProtocol.HTTPS, HTTPStreamProvider)
    StreamProviderFactory.register(StreamProtocol.FILE, FileStreamProvider)


# Auto-register on import
register_all()

"""
Base classes for real-time AI recognition system.

Defines abstract interfaces and data structures for a modular,
extensible real-time AI recognition framework.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, AsyncIterator, Union
from enum import Enum
import asyncio
import numpy as np


class StreamProtocol(str, Enum):
    """Supported streaming protocols"""
    RTSP = "rtsp"
    RTMP = "rtmp"
    HTTP = "http"
    HTTPS = "https"
    FILE = "file"


class DetectorType(str, Enum):
    """Available AI detector types"""
    YOLOV11_NANO = "yolov11n"
    YOLOV11_SMALL = "yolov11s" 
    YOLOV11_MEDIUM = "yolov11m"
    YOLOV11_LARGE = "yolov11l"
    YOLOV11_XLARGE = "yolov11x"
    MULTI_GPU_YOLOV11_NANO = "multi_gpu_yolov11n"
    MULTI_GPU_YOLOV11_SMALL = "multi_gpu_yolov11s"
    MULTI_GPU_YOLOV11_MEDIUM = "multi_gpu_yolov11m"
    MULTI_GPU_YOLOV11_LARGE = "multi_gpu_yolov11l"
    MULTI_GPU_YOLOV11_XLARGE = "multi_gpu_yolov11x"
    VEHICLE_DETECTOR = "vehicle_detector"
    MULTI_VEHICLE_TYPE = "multi_vehicle_type"
    CUSTOM = "custom"


@dataclass
class BoundingBox:
    """Bounding box representation"""
    x1: float
    y1: float
    x2: float
    y2: float
    
    @property
    def width(self) -> float:
        return self.x2 - self.x1
    
    @property
    def height(self) -> float:
        return self.y2 - self.y1
    
    @property
    def center(self) -> tuple[float, float]:
        return ((self.x1 + self.x2) / 2, (self.y1 + self.y2) / 2)
    
    @property
    def area(self) -> float:
        return self.width * self.height


@dataclass
class Detection:
    """Single object detection result"""
    bbox: BoundingBox
    confidence: float
    class_id: int
    class_name: str
    additional_info: Optional[Dict[str, Any]] = None


@dataclass
class DetectionResult:
    """Complete detection result for a frame"""
    frame_id: int
    timestamp: float
    detections: List[Detection]
    frame_width: int
    frame_height: int
    processing_time_ms: float
    model_info: Dict[str, Any]
    
    @property
    def total_objects(self) -> int:
        return len(self.detections)
    
    @property
    def confidence_scores(self) -> List[float]:
        return [det.confidence for det in self.detections]
    
    @property
    def class_counts(self) -> Dict[str, int]:
        counts = {}
        for det in self.detections:
            counts[det.class_name] = counts.get(det.class_name, 0) + 1
        return counts


@dataclass
class StreamConfig:
    """Stream configuration"""
    url: str
    protocol: StreamProtocol
    fps: Optional[int] = None
    resolution: Optional[tuple[int, int]] = None
    timeout: int = 30
    retry_attempts: int = 3
    buffer_size: int = 1
    authentication: Optional[Dict[str, str]] = None
    additional_params: Optional[Dict[str, Any]] = None


class BaseStreamProvider(ABC):
    """Abstract base class for stream providers"""
    
    def __init__(self, config: StreamConfig):
        self.config = config
        self._is_connected = False
        self._frame_count = 0
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the stream"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close the stream connection"""
        pass
    
    @abstractmethod
    async def get_frame(self) -> Optional[np.ndarray]:
        """Get the next frame from stream"""
        pass
    
    @abstractmethod
    async def get_frame_iterator(self) -> AsyncIterator[np.ndarray]:
        """Get async iterator for frames"""
        pass
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def frame_count(self) -> int:
        return self._frame_count
    
    async def get_stream_info(self) -> Dict[str, Any]:
        """Get stream information"""
        return {
            "url": self.config.url,
            "protocol": self.config.protocol,
            "connected": self.is_connected,
            "frame_count": self.frame_count,
            "fps": self.config.fps,
            "resolution": self.config.resolution
        }


class BaseRealtimeDetector(ABC):
    """Abstract base class for real-time AI detectors"""
    
    def __init__(self, model_config: Dict[str, Any]):
        self.model_config = model_config
        self._is_loaded = False
        self._detection_count = 0
    
    @abstractmethod
    async def load_model(self) -> bool:
        """Load the AI model"""
        pass
    
    @abstractmethod
    async def unload_model(self) -> None:
        """Unload the AI model to free memory"""
        pass
    
    @abstractmethod
    async def detect_frame(self, frame: np.ndarray, frame_id: int) -> DetectionResult:
        """Detect objects in a single frame"""
        pass
    
    @abstractmethod
    async def detect_batch(self, frames: List[np.ndarray], frame_ids: List[int]) -> List[DetectionResult]:
        """Detect objects in multiple frames (batch processing)"""
        pass
    
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
    
    @property
    def detection_count(self) -> int:
        return self._detection_count
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_type": self.__class__.__name__,
            "loaded": self.is_loaded,
            "detection_count": self.detection_count,
            "config": self.model_config
        }
    
    async def warm_up(self, dummy_frame: Optional[np.ndarray] = None) -> None:
        """Warm up the model with a dummy inference"""
        if not self.is_loaded:
            await self.load_model()
        
        if dummy_frame is None:
            # Create a dummy frame for warm-up
            dummy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        try:
            await self.detect_frame(dummy_frame, 0)
        except Exception:
            pass  # Ignore warm-up errors


class BaseRealtimeAI(ABC):
    """Abstract base class for complete real-time AI systems"""
    
    def __init__(self, detector: BaseRealtimeDetector, stream_provider: BaseStreamProvider):
        self.detector = detector
        self.stream_provider = stream_provider
        self._is_running = False
        self._task: Optional[asyncio.Task] = None
    
    @abstractmethod
    async def start_detection(self) -> None:
        """Start real-time detection"""
        pass
    
    @abstractmethod
    async def stop_detection(self) -> None:
        """Stop real-time detection"""
        pass
    
    @abstractmethod
    async def get_results_iterator(self) -> AsyncIterator[DetectionResult]:
        """Get async iterator for detection results"""
        pass
    
    @property
    def is_running(self) -> bool:
        return self._is_running
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get complete system information"""
        return {
            "running": self.is_running,
            "detector": await self.detector.get_model_info(),
            "stream": await self.stream_provider.get_stream_info()
        }

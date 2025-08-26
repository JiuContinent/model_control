"""
Core module for real-time AI recognition system.

Contains base classes, factories, and essential infrastructure.
"""

from .base import BaseRealtimeDetector, BaseStreamProvider, DetectionResult, StreamConfig
from .factory import DetectorFactory, StreamProviderFactory
from .exceptions import RealtimeAIException, StreamException, DetectionException

__all__ = [
    "BaseRealtimeDetector",
    "BaseStreamProvider", 
    "DetectionResult",
    "StreamConfig",
    "DetectorFactory",
    "StreamProviderFactory",
    "RealtimeAIException",
    "StreamException", 
    "DetectionException",
]

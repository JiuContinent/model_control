"""
Utility functions for real-time AI module.
"""

from .gpu_utils import detect_gpu_info, check_gpu_availability, get_optimal_device
from .system_utils import get_system_info, check_dependencies

__all__ = [
    "detect_gpu_info",
    "check_gpu_availability", 
    "get_optimal_device",
    "get_system_info",
    "check_dependencies"
]

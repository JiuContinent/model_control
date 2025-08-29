"""
System utility functions for real-time AI module.

Provides system information and dependency checking functions.
"""

import platform
import sys
import subprocess
from typing import Dict, Any, List
from loguru import logger


def get_system_info() -> Dict[str, Any]:
    """
    Get comprehensive system information
    
    Returns:
        Dictionary containing system information
    """
    info = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "architecture": platform.architecture()[0]
        },
        "python": {
            "version": sys.version,
            "implementation": platform.python_implementation(),
            "compiler": platform.python_compiler()
        },
        "dependencies": {},
        "opencv": {},
        "ffmpeg": {}
    }
    
    # Check key dependencies
    dependencies = [
        "torch", "torchvision", "ultralytics", 
        "opencv-python", "numpy", "pillow",
        "fastapi", "uvicorn", "loguru"
    ]
    
    for dep in dependencies:
        try:
            module = __import__(dep.replace("-", "_"))
            version = getattr(module, "__version__", "unknown")
            info["dependencies"][dep] = {
                "installed": True,
                "version": version
            }
        except ImportError:
            info["dependencies"][dep] = {
                "installed": False,
                "version": None
            }
    
    # Check OpenCV build info
    try:
        import cv2
        info["opencv"] = {
            "version": cv2.__version__,
            "build_info": cv2.getBuildInformation()
        }
    except ImportError:
        info["opencv"] = {"installed": False}
    
    # Check FFmpeg availability
    info["ffmpeg"] = check_ffmpeg()
    
    return info


def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies are available
    
    Returns:
        Dictionary indicating which dependencies are available
    """
    required_deps = {
        "torch": False,
        "ultralytics": False,
        "opencv": False,
        "numpy": False,
        "fastapi": False
    }
    
    # Check PyTorch
    try:
        import torch
        required_deps["torch"] = True
    except ImportError:
        pass
    
    # Check Ultralytics YOLOv11
    try:
        from ultralytics import YOLO
        required_deps["ultralytics"] = True
    except ImportError:
        pass
    
    # Check OpenCV
    try:
        import cv2
        required_deps["opencv"] = True
    except ImportError:
        pass
    
    # Check NumPy
    try:
        import numpy
        required_deps["numpy"] = True
    except ImportError:
        pass
    
    # Check FastAPI
    try:
        import fastapi
        required_deps["fastapi"] = True
    except ImportError:
        pass
    
    return required_deps


def check_ffmpeg() -> Dict[str, Any]:
    """
    Check FFmpeg installation and capabilities
    
    Returns:
        FFmpeg information
    """
    ffmpeg_info = {
        "installed": False,
        "version": None,
        "path": None,
        "codecs": []
    }
    
    try:
        # Check if ffmpeg is in PATH
        result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            timeout=10
        )
        
        if result.returncode == 0:
            ffmpeg_info["installed"] = True
            lines = result.stdout.split('\n')
            if lines:
                # Extract version from first line
                version_line = lines[0]
                if "ffmpeg version" in version_line:
                    ffmpeg_info["version"] = version_line.split(" ")[2]
            
            # Get FFmpeg path
            path_result = subprocess.run(
                ["which", "ffmpeg"] if platform.system() != "Windows" else ["where", "ffmpeg"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if path_result.returncode == 0:
                ffmpeg_info["path"] = path_result.stdout.strip()
        
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    return ffmpeg_info


def get_optimal_worker_count() -> int:
    """
    Get optimal number of worker processes for the system
    
    Returns:
        Recommended worker count
    """
    import os
    
    cpu_count = os.cpu_count() or 1
    
    # For I/O bound tasks (like stream processing), use more workers
    # For CPU bound tasks, use fewer workers
    if cpu_count <= 2:
        return 1
    elif cpu_count <= 4:
        return 2
    elif cpu_count <= 8:
        return 4
    else:
        return min(8, cpu_count // 2)


def check_port_availability(port: int, host: str = "localhost") -> bool:
    """
    Check if a port is available
    
    Args:
        port: Port number to check
        host: Host to check (default: localhost)
        
    Returns:
        True if port is available, False otherwise
    """
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return False


def get_memory_info() -> Dict[str, float]:
    """
    Get system memory information
    
    Returns:
        Memory information in GB
    """
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        return {
            "total_gb": memory.total / (1024**3),
            "available_gb": memory.available / (1024**3),
            "used_gb": memory.used / (1024**3),
            "usage_percent": memory.percent
        }
    except ImportError:
        # Fallback method without psutil
        try:
            import os
            if hasattr(os, 'sysconf'):
                # Unix-like systems
                page_size = os.sysconf('SC_PAGE_SIZE')
                total_pages = os.sysconf('SC_PHYS_PAGES')
                available_pages = os.sysconf('SC_AVPHYS_PAGES')
                
                total_gb = (total_pages * page_size) / (1024**3)
                available_gb = (available_pages * page_size) / (1024**3)
                used_gb = total_gb - available_gb
                
                return {
                    "total_gb": total_gb,
                    "available_gb": available_gb,
                    "used_gb": used_gb,
                    "usage_percent": (used_gb / total_gb) * 100
                }
        except Exception:
            pass
        
        return {"error": "Unable to get memory info"}


def log_system_startup_info():
    """
    Log comprehensive system information at startup
    """
    logger.info("=== System Information ===")
    
    system_info = get_system_info()
    
    # Log platform info
    platform_info = system_info["platform"]
    logger.info(f"Platform: {platform_info['system']} {platform_info['release']} ({platform_info['architecture']})")
    logger.info(f"Processor: {platform_info['processor']}")
    
    # Log Python info
    python_info = system_info["python"]
    logger.info(f"Python: {python_info['implementation']} {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    
    # Log memory info
    memory_info = get_memory_info()
    if "error" not in memory_info:
        logger.info(f"Memory: {memory_info['total_gb']:.1f}GB total, {memory_info['available_gb']:.1f}GB available")
    
    # Log key dependencies
    deps = system_info["dependencies"]
    key_deps = ["torch", "ultralytics", "opencv-python"]
    for dep in key_deps:
        if dep in deps and deps[dep]["installed"]:
            logger.info(f"{dep}: {deps[dep]['version']}")
        else:
            logger.warning(f"{dep}: NOT INSTALLED")
    
    # Log GPU info
    try:
        from .gpu_utils import detect_gpu_info
        gpu_info = detect_gpu_info()
        if gpu_info["cuda_available"]:
            logger.info(f"CUDA: Available ({gpu_info['gpu_count']} GPU(s))")
            for gpu in gpu_info["gpu_devices"]:
                logger.info(f"  GPU {gpu['id']}: {gpu['name']} ({gpu['memory_total_gb']:.1f}GB)")
        elif gpu_info["mps_available"]:
            logger.info("MPS: Available (Apple Silicon)")
        else:
            logger.info("GPU: Not available, using CPU")
    except Exception as e:
        logger.warning(f"Failed to get GPU info: {e}")
    
    # Log FFmpeg info
    ffmpeg_info = system_info["ffmpeg"]
    if ffmpeg_info["installed"]:
        logger.info(f"FFmpeg: {ffmpeg_info['version']} at {ffmpeg_info['path']}")
    else:
        logger.warning("FFmpeg: NOT INSTALLED (required for RTMP streams)")
    
    logger.info("=== End System Information ===")


def validate_environment() -> List[str]:
    """
    Validate the environment for real-time AI functionality
    
    Returns:
        List of validation warnings/errors
    """
    issues = []
    
    # Check dependencies
    deps = check_dependencies()
    for dep, available in deps.items():
        if not available:
            issues.append(f"Missing required dependency: {dep}")
    
    # Check GPU availability
    try:
        from .gpu_utils import check_gpu_availability
        if not check_gpu_availability():
            issues.append("No GPU acceleration available - performance may be limited")
    except Exception:
        issues.append("Unable to check GPU availability")
    
    # Check FFmpeg for RTMP support
    ffmpeg_info = check_ffmpeg()
    if not ffmpeg_info["installed"]:
        issues.append("FFmpeg not found - RTMP streams may not work")
    
    # Check memory
    memory_info = get_memory_info()
    if "error" not in memory_info and memory_info["available_gb"] < 2:
        issues.append("Low available memory - may affect performance")
    
    return issues

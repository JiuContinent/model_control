"""
GPU detection and utility functions for real-time AI.

Provides functions to detect GPU availability, capabilities,
and recommend optimal settings for YOLOv11 inference.
"""

from typing import Dict, Any, Optional, List, Tuple
import platform
from loguru import logger


def detect_gpu_info() -> Dict[str, Any]:
    """
    Detect available GPU information with multi-GPU support
    
    Returns:
        Dictionary containing GPU information
    """
    gpu_info = {
        "cuda_available": False,
        "mps_available": False,
        "gpu_count": 0,
        "gpu_devices": [],
        "recommended_device": "cpu",
        "recommended_multi_gpu": False,
        "multi_gpu_strategy": None,
        "cuda_version": None,
        "pytorch_version": None,
        "total_gpu_memory_gb": 0.0
    }
    
    try:
        import torch
        gpu_info["pytorch_version"] = torch.__version__
        
        # Check CUDA availability
        if torch.cuda.is_available():
            gpu_info["cuda_available"] = True
            gpu_info["gpu_count"] = torch.cuda.device_count()
            gpu_info["recommended_device"] = "cuda"
            gpu_info["cuda_version"] = torch.version.cuda
            
            # Get information for each GPU
            total_memory = 0.0
            for i in range(gpu_info["gpu_count"]):
                device_props = torch.cuda.get_device_properties(i)
                memory_total = device_props.total_memory / (1024**3)
                total_memory += memory_total
                
                gpu_device = {
                    "id": i,
                    "name": device_props.name,
                    "memory_total_gb": memory_total,
                    "memory_allocated_gb": torch.cuda.memory_allocated(i) / (1024**3),
                    "memory_cached_gb": torch.cuda.memory_reserved(i) / (1024**3),
                    "compute_capability": f"{device_props.major}.{device_props.minor}",
                    "multi_processor_count": device_props.multi_processor_count,
                    "is_available": True,
                    "utilization_percent": 0.0  # Will be updated dynamically
                }
                gpu_info["gpu_devices"].append(gpu_device)
            
            gpu_info["total_gpu_memory_gb"] = total_memory
            
            # Determine multi-GPU strategy
            if gpu_info["gpu_count"] > 1:
                gpu_info["recommended_multi_gpu"] = True
                gpu_info["multi_gpu_strategy"] = _determine_multi_gpu_strategy(gpu_info["gpu_devices"])
                logger.info(f"Multi-GPU setup detected: {gpu_info['gpu_count']} GPUs, strategy: {gpu_info['multi_gpu_strategy']}")
            else:
                logger.info(f"Single GPU detected: {gpu_info['gpu_devices'][0]['name'] if gpu_info['gpu_devices'] else 'Unknown'}")
            
            logger.info(f"CUDA detected: {gpu_info['gpu_count']} GPU(s) available, total memory: {total_memory:.1f}GB")
            
        # Check MPS (Metal Performance Shaders) availability on macOS
        elif torch.backends.mps.is_available():
            gpu_info["mps_available"] = True
            gpu_info["recommended_device"] = "mps"
            logger.info("MPS (Metal Performance Shaders) available")
            
        else:
            logger.info("No GPU acceleration available, using CPU")
            
    except ImportError:
        logger.warning("PyTorch not available, cannot detect GPU")
    except Exception as e:
        logger.error(f"Error detecting GPU info: {e}")
    
    return gpu_info


def check_gpu_availability() -> bool:
    """
    Quick check if GPU is available for inference
    
    Returns:
        True if GPU is available, False otherwise
    """
    try:
        import torch
        return torch.cuda.is_available() or torch.backends.mps.is_available()
    except ImportError:
        return False


def get_optimal_device(preferred_device: Optional[str] = None) -> str:
    """
    Get optimal device for YOLOv11 inference
    
    Args:
        preferred_device: User's preferred device ('cuda', 'mps', 'cpu')
        
    Returns:
        Optimal device string
    """
    try:
        import torch
        
        # If user specifies a device, validate it
        if preferred_device:
            if preferred_device == "cuda" and torch.cuda.is_available():
                return "cuda"
            elif preferred_device == "mps" and torch.backends.mps.is_available():
                return "mps"
            elif preferred_device == "cpu":
                return "cpu"
            else:
                logger.warning(f"Requested device '{preferred_device}' not available")
        
        # Auto-select best available device
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"
            
    except ImportError:
        logger.warning("PyTorch not available")
        return "cpu"


def get_gpu_memory_info(device_id: int = 0) -> Dict[str, float]:
    """
    Get GPU memory information
    
    Args:
        device_id: GPU device ID
        
    Returns:
        Memory information in GB
    """
    try:
        import torch
        
        if not torch.cuda.is_available():
            return {"error": "CUDA not available"}
        
        if device_id >= torch.cuda.device_count():
            return {"error": f"Device {device_id} not available"}
        
        total = torch.cuda.get_device_properties(device_id).total_memory / (1024**3)
        allocated = torch.cuda.memory_allocated(device_id) / (1024**3)
        cached = torch.cuda.memory_reserved(device_id) / (1024**3)
        free = total - allocated
        
        return {
            "total_gb": total,
            "allocated_gb": allocated,
            "cached_gb": cached,
            "free_gb": free,
            "utilization_percent": (allocated / total) * 100
        }
        
    except Exception as e:
        return {"error": str(e)}


def recommend_model_settings(device: str, gpu_memory_gb: float = None) -> Dict[str, Any]:
    """
    Recommend optimal model settings based on hardware
    
    Args:
        device: Target device ('cuda', 'mps', 'cpu')
        gpu_memory_gb: Available GPU memory in GB
        
    Returns:
        Recommended settings
    """
    settings = {
        "half_precision": False,
        "batch_size": 1,
        "recommended_variants": [],
        "image_size": 640
    }
    
    if device == "cuda":
        settings["half_precision"] = True
        
        if gpu_memory_gb:
            if gpu_memory_gb >= 12:
                # High-end GPU
                settings["batch_size"] = 4
                settings["recommended_variants"] = ["yolov11x", "yolov11l", "yolov11m"]
                settings["image_size"] = 1280
            elif gpu_memory_gb >= 8:
                # Mid-range GPU
                settings["batch_size"] = 3
                settings["recommended_variants"] = ["yolov11l", "yolov11m", "yolov11s"]
                settings["image_size"] = 1024
            elif gpu_memory_gb >= 6:
                # Entry-level GPU
                settings["batch_size"] = 2
                settings["recommended_variants"] = ["yolov11m", "yolov11s", "yolov11n"]
            elif gpu_memory_gb >= 4:
                # Low-end GPU
                settings["batch_size"] = 1
                settings["recommended_variants"] = ["yolov11s", "yolov11n"]
            else:
                # Very limited GPU
                settings["batch_size"] = 1
                settings["recommended_variants"] = ["yolov11n"]
                settings["image_size"] = 416
        else:
            # Default CUDA settings
            settings["batch_size"] = 2
            settings["recommended_variants"] = ["yolov11s", "yolov11n"]
            
    elif device == "mps":
        # MPS (Apple Silicon) settings
        settings["half_precision"] = False  # MPS doesn't support FP16 well yet
        settings["batch_size"] = 2
        settings["recommended_variants"] = ["yolov11m", "yolov11s", "yolov11n"]
        
    else:
        # CPU settings
        settings["half_precision"] = False
        settings["batch_size"] = 1
        settings["recommended_variants"] = ["yolov11n", "yolov11s"]
        settings["image_size"] = 640
    
    return settings


def clear_gpu_cache(device_ids: Optional[List[int]] = None) -> bool:
    """
    Clear GPU memory cache for specified devices
    
    Args:
        device_ids: List of GPU device IDs to clear, None for all devices
    
    Returns:
        True if successful, False otherwise
    """
    try:
        import torch
        if torch.cuda.is_available():
            if device_ids is None:
                # Clear cache for all devices
                torch.cuda.empty_cache()
                logger.info("GPU cache cleared for all devices")
            else:
                # Clear cache for specific devices
                current_device = torch.cuda.current_device()
                for device_id in device_ids:
                    if device_id < torch.cuda.device_count():
                        torch.cuda.set_device(device_id)
                        torch.cuda.empty_cache()
                torch.cuda.set_device(current_device)
                logger.info(f"GPU cache cleared for devices: {device_ids}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to clear GPU cache: {e}")
        return False


def _determine_multi_gpu_strategy(gpu_devices: List[Dict]) -> str:
    """
    Determine the best multi-GPU strategy based on available hardware
    
    Args:
        gpu_devices: List of GPU device information
    
    Returns:
        Recommended multi-GPU strategy
    """
    if len(gpu_devices) < 2:
        return "single_gpu"
    
    # Check if all GPUs are similar (same memory and compute capability)
    first_gpu = gpu_devices[0]
    all_similar = True
    
    for gpu in gpu_devices[1:]:
        if (abs(gpu["memory_total_gb"] - first_gpu["memory_total_gb"]) > 1.0 or
            gpu["compute_capability"] != first_gpu["compute_capability"]):
            all_similar = False
            break
    
    if all_similar:
        if len(gpu_devices) <= 4:
            return "data_parallel"  # Best for 2-4 similar GPUs
        else:
            return "model_parallel"  # For >4 GPUs, consider model parallelism
    else:
        return "load_balancing"  # Different GPUs, use load balancing


def get_multi_gpu_devices() -> List[int]:
    """
    Get list of available GPU device IDs
    
    Returns:
        List of GPU device IDs
    """
    try:
        import torch
        if torch.cuda.is_available():
            return list(range(torch.cuda.device_count()))
        return []
    except Exception:
        return []


def get_optimal_device_distribution(gpu_count: int, stream_count: int) -> List[int]:
    """
    Get optimal device distribution for multiple streams
    
    Args:
        gpu_count: Number of available GPUs
        stream_count: Number of streams to process
    
    Returns:
        List of device IDs for each stream
    """
    if gpu_count == 0:
        return [0] * stream_count  # Use CPU (device 0 means CPU in this context)
    
    if gpu_count == 1:
        return [0] * stream_count  # Use single GPU for all streams
    
    # Distribute streams across GPUs
    device_distribution = []
    for i in range(stream_count):
        device_id = i % gpu_count
        device_distribution.append(device_id)
    
    return device_distribution


def monitor_gpu_utilization(device_ids: Optional[List[int]] = None) -> Dict[int, Dict[str, float]]:
    """
    Monitor GPU utilization for specified devices
    
    Args:
        device_ids: List of GPU device IDs to monitor, None for all devices
    
    Returns:
        Dictionary with device utilization information
    """
    utilization_info = {}
    
    try:
        import torch
        if not torch.cuda.is_available():
            return utilization_info
        
        if device_ids is None:
            device_ids = list(range(torch.cuda.device_count()))
        
        for device_id in device_ids:
            if device_id < torch.cuda.device_count():
                total_memory = torch.cuda.get_device_properties(device_id).total_memory
                allocated_memory = torch.cuda.memory_allocated(device_id)
                cached_memory = torch.cuda.memory_reserved(device_id)
                
                utilization_info[device_id] = {
                    "memory_utilization_percent": (allocated_memory / total_memory) * 100,
                    "memory_allocated_gb": allocated_memory / (1024**3),
                    "memory_cached_gb": cached_memory / (1024**3),
                    "memory_total_gb": total_memory / (1024**3),
                    "memory_free_gb": (total_memory - allocated_memory) / (1024**3)
                }
        
    except Exception as e:
        logger.error(f"Failed to monitor GPU utilization: {e}")
    
    return utilization_info


def select_best_gpu_for_task(task_memory_requirement_gb: float = 2.0) -> int:
    """
    Select the best available GPU for a task based on memory availability
    
    Args:
        task_memory_requirement_gb: Required memory for the task in GB
    
    Returns:
        Best GPU device ID, -1 if no suitable GPU found
    """
    try:
        import torch
        if not torch.cuda.is_available():
            return -1
        
        utilization = monitor_gpu_utilization()
        best_device = -1
        max_free_memory = 0.0
        
        for device_id, info in utilization.items():
            free_memory = info["memory_free_gb"]
            
            # Check if GPU has enough memory and is less utilized
            if (free_memory >= task_memory_requirement_gb and 
                free_memory > max_free_memory):
                max_free_memory = free_memory
                best_device = device_id
        
        if best_device != -1:
            logger.info(f"Selected GPU {best_device} with {max_free_memory:.1f}GB free memory")
        else:
            logger.warning(f"No GPU found with {task_memory_requirement_gb}GB free memory")
        
        return best_device
        
    except Exception as e:
        logger.error(f"Failed to select best GPU: {e}")
        return -1


def get_multi_gpu_recommendations(stream_count: int = 1) -> Dict[str, Any]:
    """
    Get multi-GPU recommendations for real-time AI processing
    
    Args:
        stream_count: Number of concurrent streams to process
    
    Returns:
        Dictionary with multi-GPU recommendations
    """
    gpu_info = detect_gpu_info()
    
    recommendations = {
        "multi_gpu_available": gpu_info["gpu_count"] > 1,
        "total_gpus": gpu_info["gpu_count"],
        "recommended_strategy": gpu_info.get("multi_gpu_strategy", "single_gpu"),
        "device_distribution": [],
        "per_gpu_streams": 1,
        "total_memory_gb": gpu_info.get("total_gpu_memory_gb", 0.0),
        "recommended_batch_size": 1
    }
    
    if gpu_info["gpu_count"] > 1:
        # Calculate optimal distribution
        recommendations["device_distribution"] = get_optimal_device_distribution(
            gpu_info["gpu_count"], stream_count
        )
        
        # Calculate streams per GPU
        recommendations["per_gpu_streams"] = max(1, stream_count // gpu_info["gpu_count"])
        
        # Adjust batch size based on total GPU memory
        total_memory = gpu_info.get("total_gpu_memory_gb", 0.0)
        if total_memory > 32:  # High-end multi-GPU setup
            recommendations["recommended_batch_size"] = 4
        elif total_memory > 16:  # Mid-range multi-GPU setup
            recommendations["recommended_batch_size"] = 2
        else:
            recommendations["recommended_batch_size"] = 1
        
        logger.info(f"Multi-GPU recommendations: {recommendations['recommended_strategy']} "
                   f"with {recommendations['per_gpu_streams']} streams per GPU")
    
    return recommendations

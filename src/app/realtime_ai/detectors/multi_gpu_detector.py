"""
Multi-GPU YOLOv11 Detector for real-time AI recognition.

Implements YOLOv11 detection with multi-GPU support for enhanced performance
in high-throughput scenarios.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from ultralytics import YOLO
from loguru import logger
import threading
from concurrent.futures import ThreadPoolExecutor

from .yolo_detector import YOLOv11Detector
from ..core.base import (
    DetectionResult, 
    Detection, 
    BoundingBox,
    DetectorType
)
from ..core.exceptions import ModelLoadException, ModelInferenceException
from ..utils.gpu_utils import (
    get_multi_gpu_devices, 
    monitor_gpu_utilization,
    select_best_gpu_for_task,
    clear_gpu_cache,
    get_multi_gpu_recommendations
)


class MultiGPUYOLOv11Detector(YOLOv11Detector):
    """Multi-GPU YOLOv11 detector with load balancing and parallel processing"""
    
    def __init__(self, model_config: Dict[str, Any]):
        # Initialize base detector
        super().__init__(model_config)
        
        # Multi-GPU specific configuration
        self.enable_multi_gpu = model_config.get("enable_multi_gpu", True)
        self.gpu_devices = model_config.get("gpu_devices", None)  # None = auto-detect
        self.load_balancing = model_config.get("load_balancing", True)
        self.parallel_streams = model_config.get("parallel_streams", 1)
        
        # Model instances for each GPU
        self.models: Dict[int, YOLO] = {}
        self.device_assignment: Dict[int, int] = {}  # stream_id -> device_id
        self.device_locks: Dict[int, threading.Lock] = {}
        self.inference_counts: Dict[int, int] = {}
        
        # Thread pool for parallel processing
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.max_workers = model_config.get("max_workers", 4)
        
        logger.info(f"MultiGPUYOLOv11Detector initialized with multi_gpu={self.enable_multi_gpu}")
    
    async def load_model(self) -> bool:
        """Load YOLOv11 models on multiple GPUs"""
        try:
            if not self.enable_multi_gpu:
                # Fall back to single GPU behavior
                return await super().load_model()
            
            # Get available GPU devices
            if self.gpu_devices is None:
                self.gpu_devices = get_multi_gpu_devices()
            
            if len(self.gpu_devices) == 0:
                logger.warning("No GPUs available, falling back to CPU")
                self.enable_multi_gpu = False
                return await super().load_model()
            
            logger.info(f"Loading models on {len(self.gpu_devices)} GPUs: {self.gpu_devices}")
            
            # Load model on each GPU
            for device_id in self.gpu_devices:
                try:
                    await self._load_model_on_device(device_id)
                    self.device_locks[device_id] = threading.Lock()
                    self.inference_counts[device_id] = 0
                    logger.info(f"Model loaded successfully on GPU {device_id}")
                except Exception as e:
                    logger.error(f"Failed to load model on GPU {device_id}: {e}")
                    # Remove failed device from list
                    if device_id in self.models:
                        del self.models[device_id]
            
            if len(self.models) == 0:
                logger.error("Failed to load model on any GPU")
                return False
            
            # Update active devices list
            self.gpu_devices = list(self.models.keys())
            logger.info(f"Successfully loaded models on {len(self.gpu_devices)} GPUs")
            
            # Initialize thread pool
            self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
            
            self._is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load multi-GPU models: {e}")
            self._is_loaded = False
            raise ModelLoadException(f"Failed to load multi-GPU models: {e}")
    
    async def _load_model_on_device(self, device_id: int) -> None:
        """Load model on specific GPU device"""
        model_path = self.model_config.get("model_path")
        
        if model_path and Path(model_path).exists():
            model = YOLO(model_path)
        else:
            model_file = self.MODEL_VARIANTS[self.model_variant]["model_file"]
            model = YOLO(model_file)
        
        # Move model to specific GPU
        model.to(f"cuda:{device_id}")
        
        # Enable half precision if supported
        if self.half_precision:
            try:
                model.half()
                logger.info(f"Half precision enabled on GPU {device_id}")
            except Exception as e:
                logger.warning(f"Half precision not supported on GPU {device_id}: {e}")
        
        self.models[device_id] = model
        
        # Warm up model on this device
        await self._warmup_model_on_device(device_id)
    
    async def _warmup_model_on_device(self, device_id: int) -> None:
        """Warm up model on specific device"""
        try:
            import torch
            
            logger.info(f"Warming up model on GPU {device_id}...")
            model = self.models[device_id]
            
            # Create dummy input on the correct device
            dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            # Set device context
            with torch.cuda.device(device_id):
                for i in range(3):
                    start_time = time.time()
                    results = model(
                        dummy_frame,
                        conf=self.confidence_threshold,
                        iou=self.iou_threshold,
                        device=f"cuda:{device_id}",
                        verbose=False
                    )
                    warmup_time = time.time() - start_time
                    logger.info(f"GPU {device_id} warmup {i+1}/3: {warmup_time*1000:.1f}ms")
                
                # Clear cache after warmup
                torch.cuda.empty_cache()
                
        except Exception as e:
            logger.warning(f"Model warmup failed on GPU {device_id}: {e}")
    
    def _select_device_for_inference(self, stream_id: int = 0) -> int:
        """Select the best GPU device for inference"""
        if not self.enable_multi_gpu or len(self.gpu_devices) == 1:
            return self.gpu_devices[0] if self.gpu_devices else 0
        
        if self.load_balancing:
            # Use load balancing - select device with least inference count
            best_device = min(self.gpu_devices, key=lambda d: self.inference_counts.get(d, 0))
            return best_device
        else:
            # Round-robin assignment
            device_index = stream_id % len(self.gpu_devices)
            return self.gpu_devices[device_index]
    
    async def detect_frame(self, frame: np.ndarray, frame_id: int, stream_id: int = 0) -> DetectionResult:
        """Detect objects in a single frame using multi-GPU"""
        if not self._is_loaded:
            raise ModelInferenceException("Models not loaded", frame_id=frame_id)
        
        if not self.enable_multi_gpu:
            return await super().detect_frame(frame, frame_id)
        
        try:
            # Select device for this inference
            device_id = self._select_device_for_inference(stream_id)
            
            start_time = time.time()
            
            # Run inference on selected device
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.thread_pool,
                self._inference_on_device,
                device_id, frame, frame_id
            )
            
            inference_time = time.time() - start_time
            self._last_inference_time = inference_time
            self._inference_times.append(inference_time)
            
            # Keep only recent inference times
            if len(self._inference_times) > 100:
                self._inference_times = self._inference_times[-100:]
            
            # Update inference count for load balancing
            self.inference_counts[device_id] = self.inference_counts.get(device_id, 0) + 1
            self._detection_count += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Multi-GPU inference failed for frame {frame_id}: {e}")
            raise ModelInferenceException(f"Multi-GPU inference failed: {e}", frame_id=frame_id)
    
    def _inference_on_device(self, device_id: int, frame: np.ndarray, frame_id: int) -> DetectionResult:
        """Synchronous inference on specific device"""
        import torch
        
        try:
            with self.device_locks[device_id]:
                model = self.models[device_id]
                
                # Set device context
                with torch.cuda.device(device_id):
                    results = model(
                        frame,
                        conf=self.confidence_threshold,
                        iou=self.iou_threshold,
                        max_det=self.max_detections,
                        classes=self.classes,
                        device=f"cuda:{device_id}",
                        half=self.half_precision,
                        imgsz=self.imgsz,
                        verbose=False
                    )
                
                # Process results
                detections = self._process_results(results[0] if results else None)
                
                return DetectionResult(
                    frame_id=frame_id,
                    timestamp=time.time(),
                    detections=detections,
                    frame_width=frame.shape[1],
                    frame_height=frame.shape[0],
                    processing_time_ms=0,  # Will be set by caller
                    model_info={
                        "model_type": "MultiGPU-YOLOv11",
                        "variant": self.model_variant,
                        "device": f"cuda:{device_id}",
                        "confidence_threshold": self.confidence_threshold,
                        "iou_threshold": self.iou_threshold,
                        "half_precision": self.half_precision,
                        "gpu_devices": self.gpu_devices,
                        "load_balancing": self.load_balancing
                    }
                )
                
        except Exception as e:
            logger.error(f"Inference failed on GPU {device_id}: {e}")
            raise
    
    async def detect_batch(self, frames: List[np.ndarray], frame_ids: List[int], stream_ids: Optional[List[int]] = None) -> List[DetectionResult]:
        """Detect objects in multiple frames using multi-GPU parallel processing"""
        if not self._is_loaded:
            raise ModelInferenceException("Models not loaded")
        
        if not self.enable_multi_gpu:
            return await super().detect_batch(frames, frame_ids)
        
        if stream_ids is None:
            stream_ids = list(range(len(frames)))
        
        try:
            # Create detection tasks for parallel execution
            tasks = []
            for frame, frame_id, stream_id in zip(frames, frame_ids, stream_ids):
                task = self.detect_frame(frame, frame_id, stream_id)
                tasks.append(task)
            
            # Execute all tasks in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Multi-GPU batch detection failed for frame {frame_ids[i]}: {result}")
                    # Create empty result for failed frame
                    processed_results.append(DetectionResult(
                        frame_id=frame_ids[i],
                        timestamp=time.time(),
                        detections=[],
                        frame_width=frames[i].shape[1] if i < len(frames) else 0,
                        frame_height=frames[i].shape[0] if i < len(frames) else 0,
                        processing_time_ms=0,
                        model_info={"error": str(result)}
                    ))
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Multi-GPU batch detection failed: {e}")
            raise ModelInferenceException(f"Multi-GPU batch detection failed: {e}")
    
    async def unload_model(self) -> None:
        """Unload models from all GPUs"""
        try:
            # Shut down thread pool
            if self.thread_pool:
                self.thread_pool.shutdown(wait=True)
                self.thread_pool = None
            
            # Unload models from each GPU
            for device_id, model in self.models.items():
                try:
                    del model
                    clear_gpu_cache([device_id])
                    logger.info(f"Model unloaded from GPU {device_id}")
                except Exception as e:
                    logger.error(f"Error unloading model from GPU {device_id}: {e}")
            
            self.models.clear()
            self.device_locks.clear()
            self.inference_counts.clear()
            self._is_loaded = False
            
            logger.info("All multi-GPU models unloaded")
            
        except Exception as e:
            logger.error(f"Error during multi-GPU model unloading: {e}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get detailed multi-GPU model information"""
        base_info = await super().get_model_info()
        
        if self.enable_multi_gpu:
            # Get GPU utilization
            utilization = monitor_gpu_utilization(self.gpu_devices)
            
            base_info.update({
                "multi_gpu_enabled": True,
                "active_gpu_devices": self.gpu_devices,
                "total_gpu_count": len(self.gpu_devices),
                "load_balancing": self.load_balancing,
                "parallel_streams": self.parallel_streams,
                "inference_counts": self.inference_counts,
                "gpu_utilization": utilization,
                "thread_pool_workers": self.max_workers
            })
        else:
            base_info["multi_gpu_enabled"] = False
        
        return base_info
    
    def get_multi_gpu_stats(self) -> Dict[str, Any]:
        """Get multi-GPU performance statistics"""
        if not self.enable_multi_gpu:
            return {"multi_gpu_enabled": False}
        
        utilization = monitor_gpu_utilization(self.gpu_devices)
        
        total_inferences = sum(self.inference_counts.values())
        load_distribution = {}
        for device_id in self.gpu_devices:
            count = self.inference_counts.get(device_id, 0)
            load_distribution[f"gpu_{device_id}"] = {
                "inference_count": count,
                "load_percentage": (count / max(total_inferences, 1)) * 100
            }
        
        return {
            "multi_gpu_enabled": True,
            "active_devices": self.gpu_devices,
            "total_inferences": total_inferences,
            "load_distribution": load_distribution,
            "gpu_utilization": utilization,
            "average_inference_time_ms": np.mean(self._inference_times) * 1000 if self._inference_times else 0
        }

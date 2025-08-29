"""
YOLOv11 Detector for real-time AI recognition.

Implements various YOLOv11 model variants (nano, small, medium, large, xlarge)
with optimized real-time inference capabilities.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from ultralytics import YOLO
from loguru import logger

from ..core.base import (
    BaseRealtimeDetector, 
    DetectionResult, 
    Detection, 
    BoundingBox,
    DetectorType
)
from ..core.exceptions import ModelLoadException, ModelInferenceException


class YOLOv11Detector(BaseRealtimeDetector):
    """YOLOv11 detector with support for different model variants"""
    
    # Model variant specifications
    MODEL_VARIANTS = {
        DetectorType.YOLOV11_NANO: {
            "model_file": "yolov11n.pt",
            "description": "Nano - Fastest, lowest accuracy",
            "params": "2.6M",
            "size_mb": 6
        },
        DetectorType.YOLOV11_SMALL: {
            "model_file": "yolov11s.pt", 
            "description": "Small - Fast, good balance",
            "params": "9.4M",
            "size_mb": 22
        },
        DetectorType.YOLOV11_MEDIUM: {
            "model_file": "yolov11m.pt",
            "description": "Medium - Moderate speed, better accuracy",
            "params": "20.1M", 
            "size_mb": 50
        },
        DetectorType.YOLOV11_LARGE: {
            "model_file": "yolov11l.pt",
            "description": "Large - Slower, high accuracy",
            "params": "25.3M",
            "size_mb": 63
        },
        DetectorType.YOLOV11_XLARGE: {
            "model_file": "yolov11x.pt",
            "description": "Extra Large - Slowest, highest accuracy", 
            "params": "68.2M",
            "size_mb": 137
        }
    }
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        self.model: Optional[YOLO] = None
        self.model_variant = model_config.get("variant", DetectorType.YOLOV11_NANO)
        
        # Auto-detect best available device if not specified
        self.device = self._get_best_device(model_config.get("device"))
        
        self.confidence_threshold = model_config.get("confidence_threshold", 0.5)
        self.iou_threshold = model_config.get("iou_threshold", 0.45)
        self.max_detections = model_config.get("max_detections", 300)
        self.classes = model_config.get("classes", None)  # None for all classes
        
        # Auto-enable half precision for GPU
        self.half_precision = model_config.get("half_precision", self.device == "cuda")
        self.imgsz = model_config.get("imgsz", 640)
        
        # Performance tracking
        self._inference_times = []
        self._last_inference_time = 0.0
        
        # Validate model variant
        if self.model_variant not in self.MODEL_VARIANTS:
            raise ModelLoadException(
                f"Unsupported model variant: {self.model_variant}. "
                f"Available variants: {list(self.MODEL_VARIANTS.keys())}"
            )
        
        logger.info(f"YOLOv11Detector initialized with device: {self.device}, half_precision: {self.half_precision}")
    
    def _get_best_device(self, requested_device: Optional[str] = None) -> str:
        """Auto-detect the best available device"""
        import torch
        
        if requested_device:
            # User specified a device, validate it
            if requested_device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available, falling back to CPU")
                return "cpu"
            elif requested_device == "mps" and not torch.backends.mps.is_available():
                logger.warning("MPS requested but not available, falling back to CPU")
                return "cpu"
            else:
                return requested_device
        
        # Auto-detect best device
        if torch.cuda.is_available():
            device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            logger.info(f"CUDA available: {gpu_name} ({gpu_memory:.1f}GB)")
        elif torch.backends.mps.is_available():
            device = "mps"
            logger.info("MPS (Metal Performance Shaders) available")
        else:
            device = "cpu"
            logger.info("Using CPU for inference")
        
        return device
    
    async def _optimize_model_for_device(self) -> None:
        """Optimize model for the target device"""
        if not self.model:
            return
            
        try:
            # Move to device
            if self.device != "cpu":
                self.model.to(self.device)
                logger.info(f"Model moved to device: {self.device}")
                
                # Check GPU memory if using CUDA
                if self.device == "cuda":
                    import torch
                    torch.cuda.empty_cache()  # Clear cache
                    allocated = torch.cuda.memory_allocated(0) / (1024**3)  # GB
                    cached = torch.cuda.memory_reserved(0) / (1024**3)  # GB
                    logger.info(f"GPU memory - Allocated: {allocated:.2f}GB, Cached: {cached:.2f}GB")
            
            # Enable half precision if supported and requested
            if self.half_precision and self.device in ["cuda", "mps"]:
                try:
                    self.model.half()
                    logger.info("Half precision (FP16) enabled for faster inference")
                except Exception as e:
                    logger.warning(f"Half precision not supported: {e}")
                    self.half_precision = False
                    
        except Exception as e:
            logger.warning(f"Failed to optimize model for {self.device}: {e}")
            # Fallback to CPU
            self.device = "cpu"
            self.half_precision = False
            if self.model:
                self.model.to("cpu")
    
    async def _warmup_model(self) -> None:
        """Warm up model with dummy inference"""
        if not self.model:
            return
            
        try:
            logger.info("Warming up model for optimal performance...")
            
            # Create dummy input
            dummy_frame = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            
            # Perform warmup inferences
            warmup_times = []
            for i in range(3):
                start_time = time.time()
                
                # Run dummy inference
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._inference_sync, dummy_frame)
                
                warmup_time = time.time() - start_time
                warmup_times.append(warmup_time)
                logger.info(f"Warmup {i+1}/3: {warmup_time*1000:.1f}ms")
            
            avg_warmup_time = np.mean(warmup_times)
            logger.info(f"Model warmup completed. Average time: {avg_warmup_time*1000:.1f}ms")
            
            # Clear GPU cache after warmup
            if self.device == "cuda":
                import torch
                torch.cuda.empty_cache()
                
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    async def load_model(self) -> bool:
        """Load YOLOv11 model"""
        try:
            model_path = self.model_config.get("model_path")
            
            if model_path and Path(model_path).exists():
                # Load custom model from path
                logger.info(f"Loading custom YOLOv11 model from: {model_path}")
                self.model = YOLO(model_path)
            else:
                # Load pre-trained model variant
                model_file = self.MODEL_VARIANTS[self.model_variant]["model_file"]
                logger.info(f"Loading YOLOv11 {self.model_variant} model: {model_file}")
                self.model = YOLO(model_file)
            
            # Move to device and optimize
            await self._optimize_model_for_device()
            
            # Perform warm-up inference for better performance
            await self._warmup_model()
            
            self._is_loaded = True
            logger.info(f"YOLOv11 {self.model_variant} model loaded successfully")
            
            # Log model info
            variant_info = self.MODEL_VARIANTS[self.model_variant]
            logger.info(f"Model variant: {variant_info['description']}")
            logger.info(f"Parameters: {variant_info['params']}, Size: ~{variant_info['size_mb']}MB")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load YOLOv11 model: {e}")
            self._is_loaded = False
            raise ModelLoadException(f"Failed to load YOLOv11 model: {e}")
    
    async def unload_model(self) -> None:
        """Unload model to free memory"""
        try:
            if self.model:
                del self.model
                self.model = None
            self._is_loaded = False
            logger.info("YOLOv11 model unloaded")
        except Exception as e:
            logger.error(f"Error unloading model: {e}")
    
    async def detect_frame(self, frame: np.ndarray, frame_id: int) -> DetectionResult:
        """Detect objects in a single frame"""
        if not self._is_loaded or not self.model:
            raise ModelInferenceException(
                "Model not loaded", 
                frame_id=frame_id
            )
        
        try:
            start_time = time.time()
            
            # Run inference in executor to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self._inference_sync, 
                frame
            )
            
            inference_time = time.time() - start_time
            self._last_inference_time = inference_time
            self._inference_times.append(inference_time)
            
            # Keep only recent inference times for averaging
            if len(self._inference_times) > 100:
                self._inference_times = self._inference_times[-100:]
            
            # Process results
            detections = self._process_results(results[0] if results else None)
            
            self._detection_count += 1
            
            return DetectionResult(
                frame_id=frame_id,
                timestamp=time.time(),
                detections=detections,
                frame_width=frame.shape[1],
                frame_height=frame.shape[0],
                processing_time_ms=inference_time * 1000,
                model_info={
                    "model_type": "YOLOv11",
                    "variant": self.model_variant,
                    "device": self.device,
                    "confidence_threshold": self.confidence_threshold,
                    "iou_threshold": self.iou_threshold,
                    "half_precision": self.half_precision
                }
            )
            
        except Exception as e:
            logger.error(f"Inference failed for frame {frame_id}: {e}")
            raise ModelInferenceException(
                f"Inference failed: {e}",
                frame_id=frame_id
            )
    
    def _inference_sync(self, frame: np.ndarray) -> List:
        """Synchronous inference (run in executor)"""
        return self.model(
            frame,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            max_det=self.max_detections,
            classes=self.classes,
            device=self.device,
            half=self.half_precision,
            imgsz=self.imgsz,
            verbose=False
        )
    
    def _process_results(self, result) -> List[Detection]:
        """Process YOLO results into Detection objects"""
        detections = []
        
        if result is None or result.boxes is None:
            return detections
        
        boxes = result.boxes
        for box in boxes:
            # Extract box coordinates
            xyxy = box.xyxy[0].cpu().numpy()
            bbox = BoundingBox(
                x1=float(xyxy[0]),
                y1=float(xyxy[1]), 
                x2=float(xyxy[2]),
                y2=float(xyxy[3])
            )
            
            # Extract confidence and class
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            class_name = self.model.names[class_id]
            
            # Additional information
            additional_info = {
                "area": bbox.area,
                "center": bbox.center
            }
            
            detection = Detection(
                bbox=bbox,
                confidence=confidence,
                class_id=class_id,
                class_name=class_name,
                additional_info=additional_info
            )
            
            detections.append(detection)
        
        return detections
    
    async def detect_batch(self, frames: List[np.ndarray], frame_ids: List[int]) -> List[DetectionResult]:
        """Detect objects in multiple frames (batch processing)"""
        if not self._is_loaded or not self.model:
            raise ModelInferenceException("Model not loaded")
        
        try:
            # Process frames concurrently
            tasks = [
                self.detect_frame(frame, frame_id) 
                for frame, frame_id in zip(frames, frame_ids)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exceptions in results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Batch detection failed for frame {frame_ids[i]}: {result}")
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
            logger.error(f"Batch detection failed: {e}")
            raise ModelInferenceException(f"Batch detection failed: {e}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        base_info = await super().get_model_info()
        
        if self.model_variant in self.MODEL_VARIANTS:
            variant_info = self.MODEL_VARIANTS[self.model_variant]
            base_info.update({
                "variant": self.model_variant,
                "variant_description": variant_info["description"],
                "parameters": variant_info["params"],
                "model_size_mb": variant_info["size_mb"],
                "device": self.device,
                "confidence_threshold": self.confidence_threshold,
                "iou_threshold": self.iou_threshold,
                "max_detections": self.max_detections,
                "half_precision": self.half_precision,
                "image_size": self.imgsz,
                "classes": self.classes,
                "avg_inference_time_ms": np.mean(self._inference_times) * 1000 if self._inference_times else 0,
                "last_inference_time_ms": self._last_inference_time * 1000,
                "available_classes": list(self.model.names.values()) if self.model else []
            })
        
        return base_info
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self._inference_times:
            return {"status": "no_data"}
        
        inference_times_ms = [t * 1000 for t in self._inference_times]
        
        return {
            "avg_inference_time_ms": np.mean(inference_times_ms),
            "min_inference_time_ms": np.min(inference_times_ms),
            "max_inference_time_ms": np.max(inference_times_ms),
            "std_inference_time_ms": np.std(inference_times_ms),
            "avg_fps": 1000 / np.mean(inference_times_ms),
            "total_inferences": len(self._inference_times),
            "device": self.device,
            "half_precision": self.half_precision
        }

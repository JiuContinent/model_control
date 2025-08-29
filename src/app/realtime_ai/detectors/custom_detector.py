"""
Custom Detector for real-time AI recognition.

Provides a template and framework for implementing custom AI detection models
beyond the standard YOLO variants.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable
import numpy as np
from loguru import logger

from ..core.base import (
    BaseRealtimeDetector, 
    DetectionResult, 
    Detection, 
    BoundingBox
)
from ..core.exceptions import ModelLoadException, ModelInferenceException, ConfigurationException


class CustomDetector(BaseRealtimeDetector):
    """
    Custom detector that allows plugging in any detection model
    
    This class provides a framework for integrating custom models by accepting
    callback functions for model loading and inference.
    """
    
    def __init__(self, model_config: Dict[str, Any]):
        super().__init__(model_config)
        
        # Required callbacks
        self.load_model_callback: Optional[Callable] = model_config.get("load_model_callback")
        self.inference_callback: Optional[Callable] = model_config.get("inference_callback")
        self.unload_model_callback: Optional[Callable] = model_config.get("unload_model_callback")
        
        # Optional preprocessing/postprocessing callbacks
        self.preprocess_callback: Optional[Callable] = model_config.get("preprocess_callback")
        self.postprocess_callback: Optional[Callable] = model_config.get("postprocess_callback")
        
        # Model instance storage
        self.custom_model = None
        
        # Detection parameters
        self.confidence_threshold = model_config.get("confidence_threshold", 0.5)
        self.model_name = model_config.get("model_name", "CustomModel")
        self.model_version = model_config.get("model_version", "1.0")
        
        # Performance tracking
        self._inference_times = []
        self._last_inference_time = 0.0
        
        # Validate required callbacks
        if not self.load_model_callback:
            raise ConfigurationException(
                "load_model_callback is required for CustomDetector",
                config_key="load_model_callback"
            )
        
        if not self.inference_callback:
            raise ConfigurationException(
                "inference_callback is required for CustomDetector",
                config_key="inference_callback"
            )
    
    async def load_model(self) -> bool:
        """Load custom model using provided callback"""
        try:
            logger.info(f"Loading custom model: {self.model_name}")
            
            # Call the custom load function
            if asyncio.iscoroutinefunction(self.load_model_callback):
                self.custom_model = await self.load_model_callback(self.model_config)
            else:
                loop = asyncio.get_event_loop()
                self.custom_model = await loop.run_in_executor(
                    None, self.load_model_callback, self.model_config
                )
            
            if self.custom_model is None:
                raise ModelLoadException("Custom model loading returned None")
            
            self._is_loaded = True
            logger.info(f"Custom model {self.model_name} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load custom model: {e}")
            self._is_loaded = False
            raise ModelLoadException(f"Failed to load custom model: {e}")
    
    async def unload_model(self) -> None:
        """Unload custom model"""
        try:
            if self.unload_model_callback and self.custom_model:
                if asyncio.iscoroutinefunction(self.unload_model_callback):
                    await self.unload_model_callback(self.custom_model)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, self.unload_model_callback, self.custom_model
                    )
            
            self.custom_model = None
            self._is_loaded = False
            logger.info(f"Custom model {self.model_name} unloaded")
            
        except Exception as e:
            logger.error(f"Error unloading custom model: {e}")
    
    async def detect_frame(self, frame: np.ndarray, frame_id: int) -> DetectionResult:
        """Detect objects using custom model"""
        if not self._is_loaded or not self.custom_model:
            raise ModelInferenceException(
                "Custom model not loaded",
                frame_id=frame_id
            )
        
        try:
            start_time = time.time()
            
            # Preprocess frame if callback provided
            processed_frame = frame
            if self.preprocess_callback:
                if asyncio.iscoroutinefunction(self.preprocess_callback):
                    processed_frame = await self.preprocess_callback(frame)
                else:
                    loop = asyncio.get_event_loop()
                    processed_frame = await loop.run_in_executor(
                        None, self.preprocess_callback, frame
                    )
            
            # Run inference
            if asyncio.iscoroutinefunction(self.inference_callback):
                raw_results = await self.inference_callback(
                    self.custom_model, processed_frame, self.model_config
                )
            else:
                loop = asyncio.get_event_loop()
                raw_results = await loop.run_in_executor(
                    None, self.inference_callback, 
                    self.custom_model, processed_frame, self.model_config
                )
            
            # Postprocess results if callback provided
            processed_results = raw_results
            if self.postprocess_callback:
                if asyncio.iscoroutinefunction(self.postprocess_callback):
                    processed_results = await self.postprocess_callback(raw_results)
                else:
                    loop = asyncio.get_event_loop()
                    processed_results = await loop.run_in_executor(
                        None, self.postprocess_callback, raw_results
                    )
            
            inference_time = time.time() - start_time
            self._last_inference_time = inference_time
            self._inference_times.append(inference_time)
            
            # Keep only recent inference times
            if len(self._inference_times) > 100:
                self._inference_times = self._inference_times[-100:]
            
            # Convert results to Detection objects
            detections = self._convert_to_detections(processed_results)
            
            self._detection_count += 1
            
            return DetectionResult(
                frame_id=frame_id,
                timestamp=time.time(),
                detections=detections,
                frame_width=frame.shape[1],
                frame_height=frame.shape[0],
                processing_time_ms=inference_time * 1000,
                model_info={
                    "model_type": "Custom",
                    "model_name": self.model_name,
                    "model_version": self.model_version,
                    "confidence_threshold": self.confidence_threshold
                }
            )
            
        except Exception as e:
            logger.error(f"Custom inference failed for frame {frame_id}: {e}")
            raise ModelInferenceException(
                f"Custom inference failed: {e}",
                frame_id=frame_id
            )
    
    def _convert_to_detections(self, results: Any) -> List[Detection]:
        """
        Convert custom model results to Detection objects
        
        Expected results format:
        [
            {
                "bbox": [x1, y1, x2, y2],
                "confidence": float,
                "class_id": int,
                "class_name": str,
                "additional_info": dict (optional)
            },
            ...
        ]
        """
        detections = []
        
        if not results:
            return detections
        
        try:
            # Handle different result formats
            if isinstance(results, dict) and "detections" in results:
                results = results["detections"]
            
            for result in results:
                if isinstance(result, dict):
                    # Extract bounding box
                    bbox_coords = result.get("bbox", [0, 0, 0, 0])
                    if len(bbox_coords) >= 4:
                        bbox = BoundingBox(
                            x1=float(bbox_coords[0]),
                            y1=float(bbox_coords[1]),
                            x2=float(bbox_coords[2]),
                            y2=float(bbox_coords[3])
                        )
                        
                        # Extract other properties
                        confidence = float(result.get("confidence", 0.0))
                        class_id = int(result.get("class_id", 0))
                        class_name = str(result.get("class_name", f"class_{class_id}"))
                        additional_info = result.get("additional_info", {})
                        
                        # Filter by confidence threshold
                        if confidence >= self.confidence_threshold:
                            detection = Detection(
                                bbox=bbox,
                                confidence=confidence,
                                class_id=class_id,
                                class_name=class_name,
                                additional_info=additional_info
                            )
                            detections.append(detection)
            
        except Exception as e:
            logger.error(f"Error converting custom results to detections: {e}")
        
        return detections
    
    async def detect_batch(self, frames: List[np.ndarray], frame_ids: List[int]) -> List[DetectionResult]:
        """Detect objects in multiple frames"""
        if not self._is_loaded or not self.custom_model:
            raise ModelInferenceException("Custom model not loaded")
        
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
                    logger.error(f"Custom batch detection failed for frame {frame_ids[i]}: {result}")
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
            logger.error(f"Custom batch detection failed: {e}")
            raise ModelInferenceException(f"Custom batch detection failed: {e}")
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get custom model information"""
        base_info = await super().get_model_info()
        
        base_info.update({
            "model_name": self.model_name,
            "model_version": self.model_version,
            "confidence_threshold": self.confidence_threshold,
            "has_preprocessing": self.preprocess_callback is not None,
            "has_postprocessing": self.postprocess_callback is not None,
            "avg_inference_time_ms": np.mean(self._inference_times) * 1000 if self._inference_times else 0,
            "last_inference_time_ms": self._last_inference_time * 1000,
            "custom_model_loaded": self.custom_model is not None
        })
        
        return base_info


# Helper functions for common custom detector patterns

def create_torch_detector(model_path: str, 
                         device: str = "cpu",
                         class_names: List[str] = None) -> Dict[str, Any]:
    """
    Helper function to create a PyTorch-based custom detector configuration
    
    Args:
        model_path: Path to PyTorch model file
        device: Device to run on (cpu, cuda)
        class_names: List of class names
    
    Returns:
        Configuration dictionary for CustomDetector
    """
    import torch
    
    def load_model(config):
        model = torch.load(model_path, map_location=device)
        model.eval()
        return model
    
    def inference(model, frame, config):
        # This is a template - implement based on your model's requirements
        with torch.no_grad():
            # Convert frame to tensor and preprocess
            # Run inference
            # Return results in expected format
            pass
    
    def unload_model(model):
        del model
        torch.cuda.empty_cache() if device == "cuda" else None
    
    return {
        "load_model_callback": load_model,
        "inference_callback": inference,
        "unload_model_callback": unload_model,
        "model_name": f"PyTorch_Custom",
        "model_path": model_path,
        "device": device,
        "class_names": class_names or []
    }


def create_onnx_detector(model_path: str,
                        providers: List[str] = None) -> Dict[str, Any]:
    """
    Helper function to create an ONNX-based custom detector configuration
    
    Args:
        model_path: Path to ONNX model file
        providers: ONNX providers (e.g., ['CUDAExecutionProvider', 'CPUExecutionProvider'])
    
    Returns:
        Configuration dictionary for CustomDetector
    """
    try:
        import onnxruntime as ort
    except ImportError:
        raise ImportError("onnxruntime required for ONNX detector")
    
    def load_model(config):
        session = ort.InferenceSession(
            model_path, 
            providers=providers or ['CPUExecutionProvider']
        )
        return session
    
    def inference(session, frame, config):
        # This is a template - implement based on your model's requirements
        # Preprocess frame
        # Run inference with session.run()
        # Return results in expected format
        pass
    
    return {
        "load_model_callback": load_model,
        "inference_callback": inference,
        "model_name": "ONNX_Custom",
        "model_path": model_path,
        "providers": providers or ['CPUExecutionProvider']
    }

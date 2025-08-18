import asyncio
import io
from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
from loguru import logger

from app.core.exceptions import AIProcessingException
from app.core.constants import AI_MODEL_CONFIG


class AIService:

    def __init__(self):
        self.model: Optional[YOLO] = None
        self.model_config = AI_MODEL_CONFIG["yolov11"]
        self._load_model()
    
    def _load_model(self):
        
        try:
            model_path = Path(self.model_config["model_path"])
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                logger.info("Using default YOLOv11 model")
                try:
                    self.model = YOLO("yolov11n.pt")
                except Exception as model_error:
                    logger.warning(f"Failed to load YOLOv11 model: {model_error}")
                    logger.info("AI service will be available but model detection will be disabled")
                    self.model = None
            else:
                self.model = YOLO(str(model_path))
            
            if self.model:
                logger.info("YOLOv11 model loaded successfully")
            else:
                logger.info("AI service initialized without model (detection disabled)")
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            logger.info("AI service will be available but model detection will be disabled")
            self.model = None
    
    async def detect_objects(self, image_path: str) -> Dict[str, Any]:
        """Async object detection"""
        if not self.model:
            return {
                "image_path": image_path,
                "error": "AI model not available",
                "detections": [],
                "total_objects": 0,
                "model_info": {
                    "name": "YOLOv11",
                    "status": "not_loaded"
                }
            }
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, self._detect_sync, image_path
            )
            return result
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            raise AIProcessingException(f"Object detection failed: {e}")
    
    def _detect_sync(self, image_path: str) -> Dict[str, Any]:
        """Sync object detection"""
        if not self.model:
            return {
                "image_path": image_path,
                "error": "AI model not available",
                "detections": [],
                "total_objects": 0,
                "model_info": {
                    "name": "YOLOv11",
                    "status": "not_loaded"
                }
            }
        
        try:
            results = self.model(
                image_path,
                conf=self.model_config["confidence_threshold"],
                iou=self.model_config["iou_threshold"],
                max_det=self.model_config["max_det"],
                classes=self.model_config["classes"]
            )
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = {
                            "bbox": box.xyxy[0].tolist(),
                            "confidence": float(box.conf[0]),
                            "class_id": int(box.cls[0]),
                            "class_name": self.model.names[int(box.cls[0])]
                        }
                        detections.append(detection)
            
            return {
                "image_path": image_path,
                "detections": detections,
                "total_objects": len(detections),
                "model_info": {
                    "name": "YOLOv11",
                    "confidence_threshold": self.model_config["confidence_threshold"],
                    "iou_threshold": self.model_config["iou_threshold"]
                }
            }
            
        except Exception as e:
            logger.error(f"Sync detection failed: {e}")
            raise AIProcessingException(f"Sync detection failed: {e}")
    
    async def detect_batch(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Batch object detection
        
        Args:
            image_paths: List of image paths
            
        Returns:
            List of detection results
        """
        try:
            tasks = [self.detect_objects(path) for path in image_paths]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Handle exception results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Image {image_paths[i]} detection failed: {result}")
                    processed_results.append({
                        "image_path": image_paths[i],
                        "error": str(result),
                        "detections": [],
                        "total_objects": 0
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        except Exception as e:
            logger.error(f"Batch detection failed: {e}")
            raise AIProcessingException(f"Batch detection failed: {e}")
    
    async def detect_from_bytes(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Detect objects from byte data
        
        Args:
            image_bytes: Image byte data
            
        Returns:
            Detection result dictionary
        """
        if not self.model:
            return {
                "error": "AI model not available",
                "detections": [],
                "total_objects": 0,
                "model_info": {
                    "name": "YOLOv11",
                    "status": "not_loaded"
                }
            }
        
        try:
            # Convert byte data to PIL image
            image = Image.open(io.BytesIO(image_bytes))
            
            # Execute detection
            results = self.model(
                image,
                conf=self.model_config["confidence_threshold"],
                iou=self.model_config["iou_threshold"],
                max_det=self.model_config["max_det"],
                classes=self.model_config["classes"]
            )
            
            # Process results
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        detection = {
                            "bbox": box.xyxy[0].tolist(),
                            "confidence": float(box.conf[0]),
                            "class_id": int(box.cls[0]),
                            "class_name": self.model.names[int(box.cls[0])]
                        }
                        detections.append(detection)
            
            return {
                "detections": detections,
                "total_objects": len(detections),
                "model_info": {
                    "name": "YOLOv11",
                    "confidence_threshold": self.model_config["confidence_threshold"],
                    "iou_threshold": self.model_config["iou_threshold"]
                }
            }
            
        except Exception as e:
            logger.error(f"Byte data detection failed: {e}")
            raise AIProcessingException(f"Byte data detection failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "model_name": "YOLOv11",
            "model_path": self.model_config["model_path"],
            "confidence_threshold": self.model_config["confidence_threshold"],
            "iou_threshold": self.model_config["iou_threshold"],
            "max_detections": self.model_config["max_det"],
            "available_classes": list(self.model.names.values()) if self.model else [],
            "model_loaded": self.model is not None,
            "status": "loaded" if self.model else "not_loaded"
        }


# Global AI service instance
ai_service = AIService()

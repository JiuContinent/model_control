"""
Vehicle Detection Module for Real-time AI Recognition.

Specialized detector for vehicle recognition with multiple vehicle types.
Supports cars, trucks, buses, motorcycles, bicycles, etc.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Set
import numpy as np
from ultralytics import YOLO
from loguru import logger

from .yolo_detector import YOLOv11Detector
from ..core.base import (
    DetectionResult, 
    Detection, 
    BoundingBox,
    DetectorType
)
from ..core.exceptions import ModelLoadException, ModelInferenceException


class VehicleType:
    """Vehicle type constants"""
    CAR = "car"
    TRUCK = "truck"
    BUS = "bus"
    MOTORCYCLE = "motorcycle"
    BICYCLE = "bicycle"
    TRAIN = "train"
    BOAT = "boat"
    AIRPLANE = "airplane"
    
    # Vehicle categories for filtering
    GROUND_VEHICLES = {CAR, TRUCK, BUS, MOTORCYCLE, BICYCLE}
    HEAVY_VEHICLES = {TRUCK, BUS, TRAIN}
    LIGHT_VEHICLES = {CAR, MOTORCYCLE, BICYCLE}
    ALL_VEHICLES = {CAR, TRUCK, BUS, MOTORCYCLE, BICYCLE, TRAIN, BOAT, AIRPLANE}


class VehicleDetector(YOLOv11Detector):
    """Specialized vehicle detector based on YOLOv11"""
    
    # COCO dataset vehicle class IDs and names
    VEHICLE_CLASSES = {
        2: "car",
        3: "motorcycle", 
        5: "bus",
        7: "truck",
        1: "bicycle",
        4: "airplane",
        6: "train",
        8: "boat"
    }
    
    def __init__(self, model_config: Dict[str, Any]):
        # Set vehicle-specific classes if not provided
        if "classes" not in model_config or model_config["classes"] is None:
            model_config["classes"] = list(self.VEHICLE_CLASSES.keys())
        
        # Vehicle detection specific settings
        self.vehicle_types_filter = set(model_config.get("vehicle_types", VehicleType.ALL_VEHICLES))
        self.min_vehicle_size = model_config.get("min_vehicle_size", 100)  # minimum bbox area
        self.confidence_by_type = model_config.get("confidence_by_type", {})
        self.enable_tracking = model_config.get("enable_tracking", True)
        self.track_history_size = model_config.get("track_history_size", 30)
        
        # Vehicle counting and statistics
        self.vehicle_counts = {}
        self.total_detections = 0
        self.vehicle_tracks = {} if self.enable_tracking else None
        
        super().__init__(model_config)
        
        logger.info(f"VehicleDetector initialized for types: {self.vehicle_types_filter}")
    
    def _process_results(self, result) -> List[Detection]:
        """Process YOLO results specifically for vehicles"""
        detections = []
        
        if result is None or result.boxes is None:
            return detections
        
        boxes = result.boxes
        for i, box in enumerate(boxes):
            # Extract box coordinates
            xyxy = box.xyxy[0].cpu().numpy()
            bbox = BoundingBox(
                x1=float(xyxy[0]),
                y1=float(xyxy[1]), 
                x2=float(xyxy[2]),
                y2=float(xyxy[3])
            )
            
            # Check minimum size
            if bbox.area < self.min_vehicle_size:
                continue
            
            # Extract confidence and class
            confidence = float(box.conf[0].cpu().numpy())
            class_id = int(box.cls[0].cpu().numpy())
            
            # Map to vehicle type
            if class_id not in self.VEHICLE_CLASSES:
                continue
                
            vehicle_type = self.VEHICLE_CLASSES[class_id]
            
            # Filter by vehicle types
            if vehicle_type not in self.vehicle_types_filter:
                continue
            
            # Apply type-specific confidence thresholds
            min_confidence = self.confidence_by_type.get(vehicle_type, self.confidence_threshold)
            if confidence < min_confidence:
                continue
            
            # Vehicle-specific additional information
            additional_info = {
                "vehicle_type": vehicle_type,
                "area": bbox.area,
                "center": bbox.center,
                "aspect_ratio": bbox.width / bbox.height if bbox.height > 0 else 0,
                "size_category": self._categorize_vehicle_size(bbox, vehicle_type),
                "detection_id": f"vehicle_{self.total_detections}_{i}"
            }
            
            # Add tracking ID if available
            if hasattr(result, 'boxes') and hasattr(box, 'id') and box.id is not None:
                track_id = int(box.id.cpu().numpy())
                additional_info["track_id"] = track_id
                
                # Update tracking history
                if self.enable_tracking:
                    self._update_track_history(track_id, bbox.center, vehicle_type)
            
            detection = Detection(
                bbox=bbox,
                confidence=confidence,
                class_id=class_id,
                class_name=vehicle_type,
                additional_info=additional_info
            )
            
            detections.append(detection)
            
            # Update statistics
            self.vehicle_counts[vehicle_type] = self.vehicle_counts.get(vehicle_type, 0) + 1
        
        self.total_detections += len(detections)
        return detections
    
    def _categorize_vehicle_size(self, bbox: BoundingBox, vehicle_type: str) -> str:
        """Categorize vehicle size based on bounding box area and type"""
        area = bbox.area
        
        if vehicle_type in ["bicycle", "motorcycle"]:
            if area < 5000:
                return "small"
            elif area < 15000:
                return "medium"
            else:
                return "large"
        elif vehicle_type == "car":
            if area < 10000:
                return "small"
            elif area < 25000:
                return "medium"
            else:
                return "large"
        elif vehicle_type in ["truck", "bus"]:
            if area < 20000:
                return "small"
            elif area < 50000:
                return "medium"
            else:
                return "large"
        else:
            return "unknown"
    
    def _update_track_history(self, track_id: int, center: tuple, vehicle_type: str):
        """Update vehicle tracking history"""
        if self.vehicle_tracks is None:
            return
        
        if track_id not in self.vehicle_tracks:
            self.vehicle_tracks[track_id] = {
                "vehicle_type": vehicle_type,
                "history": [],
                "first_seen": time.time(),
                "last_seen": time.time()
            }
        
        track = self.vehicle_tracks[track_id]
        track["history"].append({
            "center": center,
            "timestamp": time.time()
        })
        track["last_seen"] = time.time()
        
        # Keep only recent history
        if len(track["history"]) > self.track_history_size:
            track["history"] = track["history"][-self.track_history_size:]
    
    async def detect_frame(self, frame: np.ndarray, frame_id: int) -> DetectionResult:
        """Detect vehicles in a single frame"""
        result = await super().detect_frame(frame, frame_id)
        
        # Add vehicle-specific statistics to result
        result.model_info.update({
            "detector_type": "VehicleDetector",
            "vehicle_types_detected": list(set(det.class_name for det in result.detections)),
            "vehicle_counts": self._get_current_frame_counts(result.detections),
            "total_vehicles_detected": self.total_detections,
            "tracking_enabled": self.enable_tracking,
            "active_tracks": len(self.vehicle_tracks) if self.vehicle_tracks else 0
        })
        
        return result
    
    def _get_current_frame_counts(self, detections: List[Detection]) -> Dict[str, int]:
        """Get vehicle counts for current frame"""
        counts = {}
        for detection in detections:
            vehicle_type = detection.class_name
            counts[vehicle_type] = counts.get(vehicle_type, 0) + 1
        return counts
    
    def get_vehicle_statistics(self) -> Dict[str, Any]:
        """Get comprehensive vehicle detection statistics"""
        stats = {
            "total_detections": self.total_detections,
            "vehicle_counts_by_type": self.vehicle_counts.copy(),
            "detection_settings": {
                "vehicle_types_filter": list(self.vehicle_types_filter),
                "min_vehicle_size": self.min_vehicle_size,
                "confidence_by_type": self.confidence_by_type
            }
        }
        
        if self.enable_tracking and self.vehicle_tracks:
            # Clean up old tracks
            current_time = time.time()
            active_tracks = {
                track_id: track for track_id, track in self.vehicle_tracks.items()
                if current_time - track["last_seen"] < 30  # 30 seconds timeout
            }
            self.vehicle_tracks = active_tracks
            
            stats.update({
                "tracking_enabled": True,
                "active_tracks": len(active_tracks),
                "tracks_by_type": self._get_tracks_by_type(active_tracks)
            })
        else:
            stats["tracking_enabled"] = False
        
        return stats
    
    def _get_tracks_by_type(self, tracks: Dict) -> Dict[str, int]:
        """Get track counts by vehicle type"""
        counts = {}
        for track in tracks.values():
            vehicle_type = track["vehicle_type"]
            counts[vehicle_type] = counts.get(vehicle_type, 0) + 1
        return counts
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get vehicle detector information"""
        base_info = await super().get_model_info()
        
        base_info.update({
            "detector_type": "VehicleDetector",
            "supported_vehicles": list(self.VEHICLE_CLASSES.values()),
            "filtered_vehicles": list(self.vehicle_types_filter),
            "vehicle_statistics": self.get_vehicle_statistics()
        })
        
        return base_info


class MultiVehicleTypeDetector(VehicleDetector):
    """Advanced vehicle detector with custom vehicle type classification"""
    
    def __init__(self, model_config: Dict[str, Any]):
        # Custom vehicle type mappings
        self.custom_vehicle_types = model_config.get("custom_vehicle_types", {})
        self.vehicle_size_thresholds = model_config.get("vehicle_size_thresholds", {})
        self.enable_sub_classification = model_config.get("enable_sub_classification", True)
        
        super().__init__(model_config)
    
    def _process_results(self, result) -> List[Detection]:
        """Enhanced processing with custom vehicle type classification"""
        detections = super()._process_results(result)
        
        if self.enable_sub_classification:
            for detection in detections:
                # Apply custom classification rules
                detection = self._apply_custom_classification(detection)
        
        return detections
    
    def _apply_custom_classification(self, detection: Detection) -> Detection:
        """Apply custom vehicle classification rules"""
        vehicle_type = detection.class_name
        bbox = detection.bbox
        
        # Sub-classify based on size and aspect ratio
        if vehicle_type == "car":
            if bbox.width / bbox.height > 2.5:
                detection.additional_info["sub_type"] = "sedan"
            elif bbox.height / bbox.width > 0.7:
                detection.additional_info["sub_type"] = "suv"
            else:
                detection.additional_info["sub_type"] = "hatchback"
        elif vehicle_type == "truck":
            if bbox.area > 50000:
                detection.additional_info["sub_type"] = "heavy_truck"
            else:
                detection.additional_info["sub_type"] = "light_truck"
        
        # Apply custom mappings
        if vehicle_type in self.custom_vehicle_types:
            detection.additional_info["custom_type"] = self.custom_vehicle_types[vehicle_type]
        
        return detection

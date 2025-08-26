"""
Vehicle AI Recognition API endpoints.

Specialized endpoints for vehicle detection and recognition.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime
from loguru import logger

from app.realtime_ai import (
    RealtimeAIService,
    ServiceConfig,
    DetectorType, 
    StreamProtocol,
    StreamConfig
)
from app.realtime_ai.detectors.vehicle_detector import VehicleType

router = APIRouter(prefix="/vehicle-ai", tags=["Vehicle AI"])


# Pydantic models for vehicle detection
class VehicleDetectionConfig(BaseModel):
    """Vehicle detection configuration"""
    vehicle_types: List[str] = ["car", "truck", "bus", "motorcycle", "bicycle"]
    min_vehicle_size: int = 100
    confidence_by_type: Dict[str, float] = {}
    enable_tracking: bool = True
    track_history_size: int = 30
    enable_sub_classification: bool = False


class VehicleStreamRequest(BaseModel):
    """Request for vehicle detection on stream"""
    stream_url: str
    protocol: Optional[StreamProtocol] = None
    detector_type: DetectorType = DetectorType.VEHICLE_DETECTOR
    vehicle_config: VehicleDetectionConfig = VehicleDetectionConfig()
    confidence_threshold: float = 0.5
    device: str = "auto"
    max_fps: int = 30


# Global vehicle service manager
vehicle_services: Dict[str, RealtimeAIService] = {}


@router.post("/start-detection")
async def start_vehicle_detection(
    request: VehicleStreamRequest,
    background_tasks: BackgroundTasks
):
    """
    Start vehicle detection on a stream
    
    Specialized for vehicle recognition with tracking and classification.
    """
    try:
        # Auto-detect protocol if not provided
        protocol = request.protocol
        if protocol is None:
            url_lower = request.stream_url.lower()
            if url_lower.startswith('rtsp://'):
                protocol = StreamProtocol.RTSP
            elif url_lower.startswith('rtmp://'):
                protocol = StreamProtocol.RTMP
            elif url_lower.startswith('http'):
                protocol = StreamProtocol.HTTP
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to detect protocol from URL"
                )
        
        # Create stream config
        stream_config = StreamConfig(
            url=request.stream_url,
            protocol=protocol
        )
        
        # Auto-detect device
        device = request.device
        if device == "auto":
            from app.realtime_ai.utils.gpu_utils import get_optimal_device
            device = get_optimal_device()
        
        # Create vehicle detection model config
        model_config = {
            "variant": DetectorType.YOLOV11_MEDIUM,  # Good balance for vehicles
            "confidence_threshold": request.confidence_threshold,
            "device": device,
            # Vehicle-specific settings
            "vehicle_types": request.vehicle_config.vehicle_types,
            "min_vehicle_size": request.vehicle_config.min_vehicle_size,
            "confidence_by_type": request.vehicle_config.confidence_by_type,
            "enable_tracking": request.vehicle_config.enable_tracking,
            "track_history_size": request.vehicle_config.track_history_size,
            "enable_sub_classification": request.vehicle_config.enable_sub_classification
        }
        
        # Create processing config
        processing_config = {
            "max_fps": request.max_fps,
            "skip_frames": 0,
            "batch_size": 1,
            "enable_tracking": request.vehicle_config.enable_tracking,
            "result_buffer_size": 100
        }
        
        # Create service config
        service_config = ServiceConfig(
            detector_type=request.detector_type,
            model_config=model_config,
            stream_config=stream_config,
            processing_config=processing_config
        )
        
        # Create and start service
        from app.api.realtime_ai import service_manager
        service_id = service_manager.create_service(service_config)
        service = service_manager.get_service(service_id)
        
        # Store in vehicle services
        vehicle_services[service_id] = service
        
        # Start detection in background
        background_tasks.add_task(service.start_detection)
        
        return {
            "service_id": service_id,
            "status": "starting",
            "message": "Vehicle detection service starting",
            "detector_type": request.detector_type,
            "vehicle_types": request.vehicle_config.vehicle_types,
            "tracking_enabled": request.vehicle_config.enable_tracking,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to start vehicle detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start vehicle detection: {e}")


@router.get("/statistics/{service_id}")
async def get_vehicle_statistics(service_id: str):
    """
    Get vehicle detection statistics
    
    Returns detailed statistics about detected vehicles.
    """
    try:
        if service_id not in vehicle_services:
            raise HTTPException(status_code=404, detail=f"Vehicle service {service_id} not found")
        
        service = vehicle_services[service_id]
        
        # Get detector-specific statistics
        if hasattr(service.detector, 'get_vehicle_statistics'):
            vehicle_stats = service.detector.get_vehicle_statistics()
        else:
            vehicle_stats = {"error": "Not a vehicle detector"}
        
        # Get general service info
        system_info = await service.get_system_info()
        
        return {
            "service_id": service_id,
            "vehicle_statistics": vehicle_stats,
            "system_info": system_info,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vehicle statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get vehicle statistics: {e}")


@router.get("/vehicle-types")
async def get_supported_vehicle_types():
    """
    Get supported vehicle types
    
    Returns all supported vehicle types and categories.
    """
    return {
        "supported_types": list(VehicleType.ALL_VEHICLES),
        "categories": {
            "ground_vehicles": list(VehicleType.GROUND_VEHICLES),
            "heavy_vehicles": list(VehicleType.HEAVY_VEHICLES),
            "light_vehicles": list(VehicleType.LIGHT_VEHICLES),
            "all_vehicles": list(VehicleType.ALL_VEHICLES)
        },
        "coco_classes": {
            2: "car",
            3: "motorcycle", 
            5: "bus",
            7: "truck",
            1: "bicycle",
            4: "airplane",
            6: "train",
            8: "boat"
        }
    }


@router.post("/quick-start")
async def quick_start_vehicle_detection(
    stream_url: str,
    vehicle_types: List[str] = Query(default=["car", "truck", "bus"]),
    confidence: float = Query(default=0.5, ge=0.1, le=1.0),
    enable_tracking: bool = Query(default=True),
    device: str = Query(default="auto"),
    background_tasks: BackgroundTasks = None
):
    """
    Quick start vehicle detection with minimal configuration
    
    Simplified endpoint for common vehicle detection scenarios.
    """
    try:
        # Validate vehicle types
        invalid_types = [vt for vt in vehicle_types if vt not in VehicleType.ALL_VEHICLES]
        if invalid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid vehicle types: {invalid_types}. "
                       f"Supported types: {list(VehicleType.ALL_VEHICLES)}"
            )
        
        # Create request
        request = VehicleStreamRequest(
            stream_url=stream_url,
            vehicle_config=VehicleDetectionConfig(
                vehicle_types=vehicle_types,
                enable_tracking=enable_tracking
            ),
            confidence_threshold=confidence,
            device=device
        )
        
        return await start_vehicle_detection(request, background_tasks)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quick start failed: {e}")
        raise HTTPException(status_code=500, detail=f"Quick start failed: {e}")


@router.get("/presets")
async def get_detection_presets():
    """
    Get predefined detection presets for common scenarios
    """
    return {
        "traffic_monitoring": {
            "vehicle_types": ["car", "truck", "bus", "motorcycle"],
            "confidence_threshold": 0.6,
            "min_vehicle_size": 200,
            "enable_tracking": True,
            "confidence_by_type": {
                "car": 0.5,
                "truck": 0.6,
                "bus": 0.6,
                "motorcycle": 0.4
            }
        },
        "parking_monitoring": {
            "vehicle_types": ["car", "motorcycle", "bicycle"],
            "confidence_threshold": 0.7,
            "min_vehicle_size": 500,
            "enable_tracking": False,
            "confidence_by_type": {
                "car": 0.7,
                "motorcycle": 0.6,
                "bicycle": 0.5
            }
        },
        "highway_monitoring": {
            "vehicle_types": ["car", "truck", "bus"],
            "confidence_threshold": 0.5,
            "min_vehicle_size": 100,
            "enable_tracking": True,
            "enable_sub_classification": True,
            "confidence_by_type": {
                "car": 0.5,
                "truck": 0.6,
                "bus": 0.6
            }
        },
        "comprehensive": {
            "vehicle_types": list(VehicleType.ALL_VEHICLES),
            "confidence_threshold": 0.4,
            "min_vehicle_size": 50,
            "enable_tracking": True,
            "enable_sub_classification": True
        }
    }


@router.get("/health")
async def vehicle_ai_health():
    """
    Vehicle AI service health check
    """
    try:
        return {
            "status": "healthy",
            "active_services": len(vehicle_services),
            "supported_detectors": [
                DetectorType.VEHICLE_DETECTOR,
                DetectorType.MULTI_VEHICLE_TYPE
            ],
            "supported_vehicle_types": list(VehicleType.ALL_VEHICLES),
            "timestamp": datetime.now()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }

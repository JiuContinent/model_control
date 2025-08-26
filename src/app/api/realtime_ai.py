"""
Real-time AI Recognition API endpoints.

Provides REST API for managing real-time AI detection services,
starting/stopping streams, and retrieving detection results.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import asyncio
import json
from datetime import datetime
from loguru import logger

from app.realtime_ai import (
    RealtimeAIService,
    ServiceConfig,
    DetectorType, 
    StreamProtocol,
    StreamConfig,
    create_rtsp_yolo_service,
    create_rtmp_yolo_service
)
from app.realtime_ai.core.exceptions import RealtimeAIException
from app.core.exceptions import AIProcessingException


router = APIRouter(prefix="/realtime-ai", tags=["Real-time AI"])


# Pydantic models for API
class StreamConfigRequest(BaseModel):
    url: str
    protocol: Optional[StreamProtocol] = None
    fps: Optional[int] = None
    resolution: Optional[tuple[int, int]] = None
    timeout: int = 30
    retry_attempts: int = 3
    buffer_size: int = 1


class ModelConfigRequest(BaseModel):
    variant: DetectorType = DetectorType.YOLOV11_NANO
    confidence_threshold: float = 0.5
    iou_threshold: float = 0.45
    device: str = "auto"
    max_detections: int = 300
    classes: Optional[List[int]] = None
    half_precision: bool = False
    model_path: Optional[str] = None
    # Multi-GPU specific settings
    enable_multi_gpu: bool = False
    gpu_devices: Optional[List[int]] = None
    load_balancing: bool = True
    max_workers: int = 4


class ProcessingConfigRequest(BaseModel):
    max_fps: int = 30
    skip_frames: int = 0
    batch_size: int = 1
    enable_tracking: bool = False
    result_buffer_size: int = 100


class StartDetectionRequest(BaseModel):
    stream_config: StreamConfigRequest
    model_settings: Optional[ModelConfigRequest] = None
    processing_settings: Optional[ProcessingConfigRequest] = None


class ServiceResponse(BaseModel):
    service_id: str
    status: str
    message: str
    timestamp: datetime


# Global service manager
class ServiceManager:
    def __init__(self):
        self.services: Dict[str, RealtimeAIService] = {}
        self.service_counter = 0
    
    def create_service(self, config: ServiceConfig) -> str:
        """Create new service and return service ID"""
        self.service_counter += 1
        service_id = f"service_{self.service_counter}"
        
        service = RealtimeAIService(config)
        self.services[service_id] = service
        
        logger.info(f"Created service {service_id}")
        return service_id
    
    def get_service(self, service_id: str) -> Optional[RealtimeAIService]:
        """Get service by ID"""
        return self.services.get(service_id)
    
    def remove_service(self, service_id: str) -> bool:
        """Remove service"""
        if service_id in self.services:
            service = self.services[service_id]
            # Cleanup will be handled by background task
            del self.services[service_id]
            logger.info(f"Removed service {service_id}")
            return True
        return False
    
    def list_services(self) -> List[str]:
        """List all service IDs"""
        return list(self.services.keys())


# Global service manager instance
service_manager = ServiceManager()


@router.post("/start", response_model=ServiceResponse)
async def start_detection(
    request: StartDetectionRequest,
    background_tasks: BackgroundTasks
):
    """
    Start real-time AI detection on a stream
    
    Creates a new detection service and starts processing the specified stream.
    Returns a service ID that can be used to manage the service.
    """
    try:
        # Create stream config
        stream_config = StreamConfig(
            url=request.stream_config.url,
            protocol=request.stream_config.protocol,
            fps=request.stream_config.fps,
            resolution=request.stream_config.resolution,
            timeout=request.stream_config.timeout,
            retry_attempts=request.stream_config.retry_attempts,
            buffer_size=request.stream_config.buffer_size
        )
        
        # Auto-detect protocol if not provided
        if stream_config.protocol is None:
            url_lower = stream_config.url.lower()
            if url_lower.startswith('rtsp://'):
                stream_config.protocol = StreamProtocol.RTSP
            elif url_lower.startswith('rtmp://'):
                stream_config.protocol = StreamProtocol.RTMP
            elif url_lower.startswith('http'):
                stream_config.protocol = StreamProtocol.HTTP
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Unable to detect protocol from URL. Please specify protocol explicitly."
                )
        
        # Use default configs if not provided
        model_config_req = request.model_settings or ModelConfigRequest()
        processing_config_req = request.processing_settings or ProcessingConfigRequest()
        
        # Auto-detect device if set to "auto"
        device = model_config_req.device
        if device == "auto":
            from app.realtime_ai.utils.gpu_utils import get_optimal_device
            device = get_optimal_device()
        
        # Create model configuration
        model_configuration = {
            "variant": model_config_req.variant,
            "confidence_threshold": model_config_req.confidence_threshold,
            "iou_threshold": model_config_req.iou_threshold,
            "device": device,
            "max_detections": model_config_req.max_detections,
            "classes": model_config_req.classes,
            "half_precision": model_config_req.half_precision,
            # Multi-GPU settings
            "enable_multi_gpu": model_config_req.enable_multi_gpu,
            "gpu_devices": model_config_req.gpu_devices,
            "load_balancing": model_config_req.load_balancing,
            "max_workers": model_config_req.max_workers
        }
        
        if model_config_req.model_path:
            model_configuration["model_path"] = model_config_req.model_path
        
        # Create processing config
        processing_config = {
            "max_fps": processing_config_req.max_fps,
            "skip_frames": processing_config_req.skip_frames,
            "batch_size": processing_config_req.batch_size,
            "enable_tracking": processing_config_req.enable_tracking,
            "result_buffer_size": processing_config_req.result_buffer_size
        }
        
        # Create service config
        service_config = ServiceConfig(
            detector_type=model_config_req.variant,
            model_config=model_configuration,
            stream_config=stream_config,
            processing_config=processing_config
        )
        
        # Create and start service
        service_id = service_manager.create_service(service_config)
        service = service_manager.get_service(service_id)
        
        # Start detection in background
        background_tasks.add_task(service.start_detection)
        
        return ServiceResponse(
            service_id=service_id,
            status="starting",
            message="Detection service starting",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to start detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start detection: {e}")


@router.post("/stop/{service_id}", response_model=ServiceResponse)
async def stop_detection(service_id: str, background_tasks: BackgroundTasks):
    """
    Stop real-time AI detection service
    
    Stops the specified detection service and cleans up resources.
    """
    try:
        service = service_manager.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        # Stop detection in background
        background_tasks.add_task(service.stop_detection)
        background_tasks.add_task(service.cleanup)
        
        # Schedule service removal
        async def cleanup_service():
            await asyncio.sleep(5)  # Wait for cleanup to complete
            service_manager.remove_service(service_id)
        
        background_tasks.add_task(cleanup_service)
        
        return ServiceResponse(
            service_id=service_id,
            status="stopping",
            message="Detection service stopping",
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop detection: {e}")


@router.get("/status/{service_id}")
async def get_service_status(service_id: str):
    """
    Get status of a detection service
    
    Returns detailed information about the service including performance statistics.
    """
    try:
        service = service_manager.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        system_info = await service.get_system_info()
        performance_stats = service.get_performance_stats()
        
        return {
            "service_id": service_id,
            "system_info": system_info,
            "performance_stats": performance_stats,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get service status: {e}")


@router.get("/services")
async def list_services():
    """
    List all active detection services
    
    Returns a list of all currently active detection services with their basic info.
    """
    try:
        services = []
        for service_id in service_manager.list_services():
            service = service_manager.get_service(service_id)
            if service:
                services.append({
                    "service_id": service_id,
                    "status": service.status,
                    "detector_type": service.config.detector_type,
                    "stream_protocol": service.config.stream_config.protocol,
                    "stream_url": service.config.stream_config.url
                })
        
        return {
            "services": services,
            "total_count": len(services),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to list services: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list services: {e}")


@router.get("/results/{service_id}")
async def get_latest_result(service_id: str, timeout: float = Query(1.0, ge=0.1, le=10.0)):
    """
    Get the latest detection result from a service
    
    Returns the most recent detection result or waits up to timeout seconds for a new result.
    """
    try:
        service = service_manager.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        result = await service.get_latest_result(timeout=timeout)
        
        if result is None:
            return {
                "service_id": service_id,
                "result": None,
                "message": "No recent results available",
                "timestamp": datetime.now()
            }
        
        # Convert result to JSON-serializable format
        result_dict = {
            "frame_id": result.frame_id,
            "timestamp": result.timestamp,
            "detections": [
                {
                    "bbox": {
                        "x1": det.bbox.x1,
                        "y1": det.bbox.y1,
                        "x2": det.bbox.x2,
                        "y2": det.bbox.y2,
                        "width": det.bbox.width,
                        "height": det.bbox.height,
                        "area": det.bbox.area,
                        "center": det.bbox.center
                    },
                    "confidence": det.confidence,
                    "class_id": det.class_id,
                    "class_name": det.class_name,
                    "additional_info": det.additional_info
                }
                for det in result.detections
            ],
            "frame_dimensions": {
                "width": result.frame_width,
                "height": result.frame_height
            },
            "processing_time_ms": result.processing_time_ms,
            "total_objects": result.total_objects,
            "class_counts": result.class_counts,
            "model_info": result.model_info
        }
        
        return {
            "service_id": service_id,
            "result": result_dict,
            "timestamp": datetime.now()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get result: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get result: {e}")


@router.get("/results/{service_id}/stream")
async def stream_results(service_id: str):
    """
    Stream detection results in real-time
    
    Returns a Server-Sent Events (SSE) stream of detection results.
    Use with EventSource in JavaScript for real-time updates.
    """
    try:
        service = service_manager.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        async def generate_results():
            try:
                async for result in service.get_results_iterator():
                    # Convert result to JSON
                    result_dict = {
                        "frame_id": result.frame_id,
                        "timestamp": result.timestamp,
                        "detections": [
                            {
                                "bbox": {
                                    "x1": det.bbox.x1,
                                    "y1": det.bbox.y1,
                                    "x2": det.bbox.x2,
                                    "y2": det.bbox.y2
                                },
                                "confidence": det.confidence,
                                "class_id": det.class_id,
                                "class_name": det.class_name
                            }
                            for det in result.detections
                        ],
                        "total_objects": result.total_objects,
                        "processing_time_ms": result.processing_time_ms
                    }
                    
                    # Format as SSE
                    data = json.dumps(result_dict)
                    yield f"data: {data}\n\n"
                    
            except Exception as e:
                logger.error(f"Error in result stream: {e}")
                error_data = json.dumps({"error": str(e)})
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_results(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start result stream: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start result stream: {e}")


@router.delete("/services/{service_id}")
async def delete_service(service_id: str, background_tasks: BackgroundTasks):
    """
    Delete a detection service
    
    Stops the service if running and removes it from the system.
    """
    try:
        service = service_manager.get_service(service_id)
        if not service:
            raise HTTPException(status_code=404, detail=f"Service {service_id} not found")
        
        # Stop and cleanup in background
        async def cleanup_and_remove():
            try:
                if service.is_running:
                    await service.stop_detection()
                await service.cleanup()
                service_manager.remove_service(service_id)
            except Exception as e:
                logger.error(f"Error during service cleanup: {e}")
        
        background_tasks.add_task(cleanup_and_remove)
        
        return ServiceResponse(
            service_id=service_id,
            status="deleted",
            message="Service marked for deletion",
            timestamp=datetime.now()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete service: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete service: {e}")


@router.get("/gpu-info")
async def get_gpu_info():
    """
    Get GPU information and capabilities including multi-GPU setup
    
    Returns detailed GPU information for optimization.
    """
    try:
        from app.realtime_ai.utils.gpu_utils import (
            detect_gpu_info, 
            recommend_model_settings,
            get_multi_gpu_recommendations,
            monitor_gpu_utilization
        )
        
        gpu_info = detect_gpu_info()
        
        # Get recommended settings for detected GPU
        device = gpu_info["recommended_device"]
        memory_gb = None
        if gpu_info["gpu_devices"]:
            memory_gb = gpu_info["gpu_devices"][0]["memory_total_gb"]
        
        recommended_settings = recommend_model_settings(device, memory_gb)
        
        # Get multi-GPU recommendations
        multi_gpu_recommendations = get_multi_gpu_recommendations()
        
        # Get current GPU utilization
        current_utilization = monitor_gpu_utilization()
        
        return {
            "gpu_info": gpu_info,
            "recommended_settings": recommended_settings,
            "multi_gpu_recommendations": multi_gpu_recommendations,
            "current_utilization": current_utilization,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get GPU info: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now()
        }


@router.get("/system-info")
async def get_system_info():
    """
    Get comprehensive system information
    
    Returns system details, dependencies, and performance capabilities.
    """
    try:
        from app.realtime_ai.utils.system_utils import get_system_info, validate_environment
        from app.realtime_ai.utils.gpu_utils import detect_gpu_info
        
        system_info = get_system_info()
        gpu_info = detect_gpu_info()
        validation_issues = validate_environment()
        
        return {
            "system": system_info,
            "gpu": gpu_info,
            "validation_issues": validation_issues,
            "environment_valid": len(validation_issues) == 0,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get system info: {e}")
        return {
            "error": str(e),
            "timestamp": datetime.now()
        }


@router.get("/health")
async def health_check():
    """
    Health check for real-time AI service
    
    Returns system health and available detector/stream types.
    """
    try:
        from app.realtime_ai.core.factory import DetectorFactory, StreamProviderFactory
        from app.realtime_ai.utils.gpu_utils import check_gpu_availability
        
        gpu_available = check_gpu_availability()
        
        return {
            "status": "healthy",
            "active_services": len(service_manager.list_services()),
            "available_detectors": DetectorFactory.get_available_types(),
            "available_stream_protocols": StreamProviderFactory.get_available_protocols(),
            "gpu_available": gpu_available,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now()
        }


# Convenience endpoints for common use cases

@router.post("/start-rtsp", response_model=ServiceResponse)
async def start_rtsp_detection(
    rtsp_url: str,
    model_variant: DetectorType = DetectorType.YOLOV11_NANO,
    confidence_threshold: float = 0.5,
    max_fps: int = 30,
    device: str = "cpu",
    background_tasks: BackgroundTasks = None
):
    """
    Quick start for RTSP stream detection
    
    Simplified endpoint for starting YOLO detection on RTSP streams.
    """
    try:
        service = create_rtsp_yolo_service(
            rtsp_url=rtsp_url,
            model_variant=model_variant,
            confidence_threshold=confidence_threshold,
            max_fps=max_fps,
            device=device
        )
        
        service_manager.service_counter += 1
        service_id = f"rtsp_service_{service_manager.service_counter}"
        service_manager.services[service_id] = service
        
        # Start detection in background
        background_tasks.add_task(service.start_detection)
        
        return ServiceResponse(
            service_id=service_id,
            status="starting",
            message=f"RTSP detection starting for {rtsp_url}",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to start RTSP detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start RTSP detection: {e}")


@router.post("/start-rtmp", response_model=ServiceResponse)
async def start_rtmp_detection(
    rtmp_url: str,
    model_variant: DetectorType = DetectorType.YOLOV11_NANO,
    confidence_threshold: float = 0.5,
    max_fps: int = 30,
    device: str = "cpu",
    background_tasks: BackgroundTasks = None
):
    """
    Quick start for RTMP stream detection
    
    Simplified endpoint for starting YOLO detection on RTMP streams.
    """
    try:
        service = create_rtmp_yolo_service(
            rtmp_url=rtmp_url,
            model_variant=model_variant,
            confidence_threshold=confidence_threshold,
            max_fps=max_fps,
            device=device
        )
        
        service_manager.service_counter += 1
        service_id = f"rtmp_service_{service_manager.service_counter}"
        service_manager.services[service_id] = service
        
        # Start detection in background
        background_tasks.add_task(service.start_detection)
        
        return ServiceResponse(
            service_id=service_id,
            status="starting",
            message=f"RTMP detection starting for {rtmp_url}",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to start RTMP detection: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start RTMP detection: {e}")

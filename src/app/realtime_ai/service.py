"""
Real-time AI Recognition Service

Main service class that orchestrates real-time AI detection on streaming media.
Provides high-level interface for starting/stopping detection, managing resources,
and retrieving results.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, AsyncIterator, Callable
from dataclasses import dataclass
from enum import Enum
import numpy as np
from loguru import logger

from .core.base import (
    BaseRealtimeDetector, 
    BaseStreamProvider, 
    BaseRealtimeAI,
    DetectionResult,
    StreamConfig,
    DetectorType,
    StreamProtocol
)
from .core.factory import DetectorFactory, StreamProviderFactory, create_realtime_ai_system
from .core.exceptions import RealtimeAIException, StreamException, DetectionException


class ServiceStatus(str, Enum):
    """Service status enumeration"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass 
class ServiceConfig:
    """Configuration for realtime AI service"""
    detector_type: DetectorType
    model_config: Dict[str, Any]
    stream_config: StreamConfig
    processing_config: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.processing_config is None:
            self.processing_config = {
                "max_fps": 30,
                "skip_frames": 0,
                "batch_size": 1,
                "enable_tracking": False,
                "result_buffer_size": 100
            }


class RealtimeAIService(BaseRealtimeAI):
    """
    Main real-time AI service that coordinates detection and streaming
    """
    
    def __init__(self, config: ServiceConfig):
        # Create detector and stream provider
        detector, stream_provider = create_realtime_ai_system(
            config.detector_type,
            config.model_config,
            config.stream_config
        )
        
        super().__init__(detector, stream_provider)
        
        self.config = config
        self.status = ServiceStatus.IDLE
        
        # Processing configuration
        self.max_fps = config.processing_config["max_fps"]
        self.skip_frames = config.processing_config["skip_frames"]
        self.batch_size = config.processing_config["batch_size"]
        self.enable_tracking = config.processing_config["enable_tracking"]
        self.result_buffer_size = config.processing_config["result_buffer_size"]
        
        # Internal state
        self._detection_task: Optional[asyncio.Task] = None
        self._results_queue: asyncio.Queue = asyncio.Queue(maxsize=self.result_buffer_size)
        self._frame_count = 0
        self._processed_frame_count = 0
        self._error_count = 0
        self._start_time = None
        
        # Performance tracking
        self._fps_actual = 0.0
        self._processing_times = []
        
        # Event hooks
        self.on_detection_complete: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
        self.on_status_change: Optional[Callable] = None
        
        logger.info(f"RealtimeAIService initialized with {config.detector_type} and {config.stream_config.protocol}")
    
    async def start_detection(self) -> None:
        """Start real-time detection process"""
        if self.status == ServiceStatus.RUNNING:
            logger.warning("Service already running")
            return
        
        try:
            await self._set_status(ServiceStatus.STARTING)
            
            # Load model
            if not self.detector.is_loaded:
                logger.info("Loading AI model...")
                await self.detector.load_model()
                await self.detector.warm_up()
            
            # Connect to stream
            if not self.stream_provider.is_connected:
                logger.info("Connecting to stream...")
                await self.stream_provider.connect()
            
            # Clear results queue
            while not self._results_queue.empty():
                try:
                    self._results_queue.get_nowait()
                except:
                    break
            
            # Reset counters
            self._frame_count = 0
            self._processed_frame_count = 0
            self._error_count = 0
            self._start_time = time.time()
            
            # Start detection task
            self._detection_task = asyncio.create_task(self._detection_loop())
            self._is_running = True
            
            await self._set_status(ServiceStatus.RUNNING)
            logger.info("Real-time detection started successfully")
            
        except Exception as e:
            await self._set_status(ServiceStatus.ERROR)
            logger.error(f"Failed to start detection: {e}")
            raise RealtimeAIException(f"Failed to start detection: {e}")
    
    async def stop_detection(self) -> None:
        """Stop real-time detection process"""
        if self.status != ServiceStatus.RUNNING:
            logger.warning("Service not running")
            return
        
        try:
            await self._set_status(ServiceStatus.STOPPING)
            
            # Cancel detection task
            if self._detection_task and not self._detection_task.done():
                self._detection_task.cancel()
                try:
                    await self._detection_task
                except asyncio.CancelledError:
                    pass
            
            self._is_running = False
            
            # Disconnect stream
            if self.stream_provider.is_connected:
                await self.stream_provider.disconnect()
            
            await self._set_status(ServiceStatus.IDLE)
            logger.info("Real-time detection stopped")
            
        except Exception as e:
            await self._set_status(ServiceStatus.ERROR)
            logger.error(f"Error stopping detection: {e}")
            raise RealtimeAIException(f"Error stopping detection: {e}")
    
    async def get_results_iterator(self) -> AsyncIterator[DetectionResult]:
        """Get async iterator for detection results"""
        while self._is_running or not self._results_queue.empty():
            try:
                # Wait for result with timeout
                result = await asyncio.wait_for(
                    self._results_queue.get(), 
                    timeout=1.0
                )
                yield result
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in results iterator: {e}")
                break
    
    async def get_latest_result(self, timeout: float = 1.0) -> Optional[DetectionResult]:
        """Get the latest detection result"""
        try:
            return await asyncio.wait_for(
                self._results_queue.get(),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            return None
    
    async def _detection_loop(self) -> None:
        """Main detection loop"""
        logger.info("Starting detection loop")
        frame_skip_counter = 0
        
        try:
            async for frame in self.stream_provider.get_frame_iterator():
                if not self._is_running:
                    break
                
                self._frame_count += 1
                
                # Skip frames if configured
                if self.skip_frames > 0:
                    frame_skip_counter += 1
                    if frame_skip_counter <= self.skip_frames:
                        continue
                    frame_skip_counter = 0
                
                # Control FPS
                if self.max_fps > 0:
                    await self._control_fps()
                
                # Process frame
                try:
                    start_time = time.time()
                    
                    result = await self.detector.detect_frame(frame, self._frame_count)
                    
                    processing_time = time.time() - start_time
                    self._processing_times.append(processing_time)
                    
                    # Keep only recent processing times
                    if len(self._processing_times) > 100:
                        self._processing_times = self._processing_times[-100:]
                    
                    # Calculate actual FPS
                    if len(self._processing_times) > 1:
                        avg_processing_time = np.mean(self._processing_times)
                        self._fps_actual = 1.0 / avg_processing_time if avg_processing_time > 0 else 0
                    
                    self._processed_frame_count += 1
                    
                    # Add result to queue (non-blocking)
                    try:
                        self._results_queue.put_nowait(result)
                    except asyncio.QueueFull:
                        # Remove oldest result and add new one
                        try:
                            self._results_queue.get_nowait()
                            self._results_queue.put_nowait(result)
                        except:
                            pass
                    
                    # Call detection complete hook
                    if self.on_detection_complete:
                        try:
                            if asyncio.iscoroutinefunction(self.on_detection_complete):
                                await self.on_detection_complete(result)
                            else:
                                self.on_detection_complete(result)
                        except Exception as e:
                            logger.error(f"Error in detection complete hook: {e}")
                
                except Exception as e:
                    self._error_count += 1
                    logger.error(f"Error processing frame {self._frame_count}: {e}")
                    
                    # Call error hook
                    if self.on_error:
                        try:
                            if asyncio.iscoroutinefunction(self.on_error):
                                await self.on_error(e)
                            else:
                                self.on_error(e)
                        except Exception as hook_error:
                            logger.error(f"Error in error hook: {hook_error}")
                    
                    # Stop if too many errors
                    if self._error_count > 10:
                        logger.error("Too many errors, stopping detection")
                        break
        
        except Exception as e:
            logger.error(f"Detection loop error: {e}")
            await self._set_status(ServiceStatus.ERROR)
        
        logger.info("Detection loop ended")
    
    async def _control_fps(self) -> None:
        """Control processing FPS"""
        if not hasattr(self, '_last_process_time'):
            self._last_process_time = time.time()
            return
        
        target_interval = 1.0 / self.max_fps
        current_time = time.time()
        elapsed = current_time - self._last_process_time
        
        if elapsed < target_interval:
            await asyncio.sleep(target_interval - elapsed)
        
        self._last_process_time = time.time()
    
    async def _set_status(self, status: ServiceStatus) -> None:
        """Set service status and call hook"""
        if self.status != status:
            old_status = self.status
            self.status = status
            logger.info(f"Service status changed: {old_status} -> {status}")
            
            if self.on_status_change:
                try:
                    if asyncio.iscoroutinefunction(self.on_status_change):
                        await self.on_status_change(old_status, status)
                    else:
                        self.on_status_change(old_status, status)
                except Exception as e:
                    logger.error(f"Error in status change hook: {e}")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        base_info = await super().get_system_info()
        
        # Add service-specific information
        runtime = time.time() - self._start_time if self._start_time else 0
        
        base_info.update({
            "service_status": self.status,
            "config": {
                "detector_type": self.config.detector_type,
                "stream_protocol": self.config.stream_config.protocol,
                "max_fps": self.max_fps,
                "skip_frames": self.skip_frames,
                "batch_size": self.batch_size,
                "enable_tracking": self.enable_tracking
            },
            "statistics": {
                "runtime_seconds": runtime,
                "total_frames": self._frame_count,
                "processed_frames": self._processed_frame_count,
                "error_count": self._error_count,
                "processing_fps": self._fps_actual,
                "avg_processing_time_ms": np.mean(self._processing_times) * 1000 if self._processing_times else 0,
                "results_queue_size": self._results_queue.qsize(),
                "success_rate": (self._processed_frame_count / max(self._frame_count, 1)) * 100
            }
        })
        
        return base_info
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed performance statistics"""
        runtime = time.time() - self._start_time if self._start_time else 0
        
        return {
            "runtime_seconds": runtime,
            "total_frames_received": self._frame_count,
            "frames_processed": self._processed_frame_count,
            "frames_skipped": self._frame_count - self._processed_frame_count,
            "error_count": self._error_count,
            "success_rate_percent": (self._processed_frame_count / max(self._frame_count, 1)) * 100,
            "processing_fps": self._fps_actual,
            "target_fps": self.max_fps,
            "avg_processing_time_ms": np.mean(self._processing_times) * 1000 if self._processing_times else 0,
            "min_processing_time_ms": np.min(self._processing_times) * 1000 if self._processing_times else 0,
            "max_processing_time_ms": np.max(self._processing_times) * 1000 if self._processing_times else 0,
            "results_queue_size": self._results_queue.qsize(),
            "results_queue_max_size": self.result_buffer_size
        }
    
    async def cleanup(self) -> None:
        """Clean up resources"""
        try:
            if self._is_running:
                await self.stop_detection()
            
            # Unload model if needed
            if self.detector.is_loaded:
                await self.detector.unload_model()
            
            logger.info("Service cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Convenience functions for creating common service configurations

def create_rtsp_yolo_service(
    rtsp_url: str,
    model_variant: DetectorType = DetectorType.YOLOV11_NANO,
    confidence_threshold: float = 0.5,
    max_fps: int = 30,
    **kwargs
) -> RealtimeAIService:
    """Create service for RTSP stream with YOLO detection"""
    
    stream_config = StreamConfig(
        url=rtsp_url,
        protocol=StreamProtocol.RTSP,
        **kwargs.get('stream_params', {})
    )
    
    model_config = {
        "variant": model_variant,
        "confidence_threshold": confidence_threshold,
        "device": kwargs.get('device', 'cpu'),
        **kwargs.get('model_params', {})
    }
    
    processing_config = {
        "max_fps": max_fps,
        "skip_frames": kwargs.get('skip_frames', 0),
        "batch_size": kwargs.get('batch_size', 1),
        **kwargs.get('processing_params', {})
    }
    
    service_config = ServiceConfig(
        detector_type=model_variant,
        model_config=model_config,
        stream_config=stream_config,
        processing_config=processing_config
    )
    
    return RealtimeAIService(service_config)


def create_rtmp_yolo_service(
    rtmp_url: str,
    model_variant: DetectorType = DetectorType.YOLOV11_NANO,
    confidence_threshold: float = 0.5,
    max_fps: int = 30,
    **kwargs
) -> RealtimeAIService:
    """Create service for RTMP stream with YOLO detection"""
    
    stream_config = StreamConfig(
        url=rtmp_url,
        protocol=StreamProtocol.RTMP,
        **kwargs.get('stream_params', {})
    )
    
    model_config = {
        "variant": model_variant,
        "confidence_threshold": confidence_threshold,
        "device": kwargs.get('device', 'cpu'),
        **kwargs.get('model_params', {})
    }
    
    processing_config = {
        "max_fps": max_fps,
        "skip_frames": kwargs.get('skip_frames', 0),
        "batch_size": kwargs.get('batch_size', 1),
        **kwargs.get('processing_params', {})
    }
    
    service_config = ServiceConfig(
        detector_type=model_variant,
        model_config=model_config,
        stream_config=stream_config,
        processing_config=processing_config
    )
    
    return RealtimeAIService(service_config)

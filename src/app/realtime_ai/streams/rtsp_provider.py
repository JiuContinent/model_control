"""
RTSP Stream Provider for real-time AI recognition.

Handles RTSP (Real Time Streaming Protocol) streams using OpenCV.
"""

import asyncio
import time
from typing import Optional, AsyncIterator
import cv2
import numpy as np
from loguru import logger

from ..core.base import BaseStreamProvider, StreamConfig, StreamProtocol
from ..core.exceptions import StreamConnectionException, StreamTimeoutException


class RTSPStreamProvider(BaseStreamProvider):
    """RTSP stream provider using OpenCV"""
    
    def __init__(self, config: StreamConfig):
        super().__init__(config)
        self.cap: Optional[cv2.VideoCapture] = None
        self._last_frame_time = 0
        self._fps_actual = 0.0
        
        # Validate RTSP URL
        if not config.url.startswith('rtsp://'):
            raise StreamConnectionException(
                f"Invalid RTSP URL: {config.url}. Must start with 'rtsp://'",
                stream_url=config.url
            )
    
    async def connect(self) -> bool:
        """Establish connection to RTSP stream"""
        try:
            # Configure OpenCV for RTSP
            self.cap = cv2.VideoCapture(self.config.url)
            
            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, self.config.buffer_size)
            
            # Set FPS if specified
            if self.config.fps:
                self.cap.set(cv2.CAP_PROP_FPS, self.config.fps)
            
            # Set resolution if specified  
            if self.config.resolution:
                width, height = self.config.resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Test connection with timeout
            start_time = time.time()
            ret, frame = self.cap.read()
            
            if time.time() - start_time > self.config.timeout:
                await self.disconnect()
                raise StreamTimeoutException(
                    f"RTSP connection timeout after {self.config.timeout}s",
                    stream_url=self.config.url,
                    timeout=self.config.timeout
                )
            
            if not ret or frame is None:
                await self.disconnect()
                raise StreamConnectionException(
                    f"Failed to read first frame from RTSP stream: {self.config.url}",
                    stream_url=self.config.url
                )
            
            self._is_connected = True
            self._last_frame_time = time.time()
            
            logger.info(f"Successfully connected to RTSP stream: {self.config.url}")
            return True
            
        except Exception as e:
            await self.disconnect()
            if isinstance(e, (StreamConnectionException, StreamTimeoutException)):
                raise
            raise StreamConnectionException(
                f"Failed to connect to RTSP stream: {e}",
                stream_url=self.config.url
            )
    
    async def disconnect(self) -> None:
        """Close RTSP stream connection"""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            self._is_connected = False
            logger.info(f"Disconnected from RTSP stream: {self.config.url}")
        except Exception as e:
            logger.error(f"Error during RTSP disconnect: {e}")
    
    async def get_frame(self) -> Optional[np.ndarray]:
        """Get next frame from RTSP stream"""
        if not self._is_connected or not self.cap:
            raise StreamConnectionException(
                "RTSP stream not connected",
                stream_url=self.config.url
            )
        
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self.cap.read)
            
            if not ret or frame is None:
                logger.warning(f"Failed to read frame from RTSP stream: {self.config.url}")
                return None
            
            self._frame_count += 1
            
            # Calculate actual FPS
            current_time = time.time()
            if self._last_frame_time > 0:
                time_diff = current_time - self._last_frame_time
                if time_diff > 0:
                    self._fps_actual = 1.0 / time_diff
            self._last_frame_time = current_time
            
            return frame
            
        except Exception as e:
            logger.error(f"Error reading RTSP frame: {e}")
            return None
    
    async def get_frame_iterator(self) -> AsyncIterator[np.ndarray]:
        """Get async iterator for RTSP frames"""
        retry_count = 0
        
        while self._is_connected and retry_count < self.config.retry_attempts:
            try:
                frame = await self.get_frame()
                if frame is not None:
                    retry_count = 0  # Reset retry count on success
                    yield frame
                else:
                    retry_count += 1
                    if retry_count >= self.config.retry_attempts:
                        logger.error(f"Max retry attempts reached for RTSP stream: {self.config.url}")
                        break
                    await asyncio.sleep(0.1)  # Brief pause before retry
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error in RTSP frame iterator (attempt {retry_count}): {e}")
                if retry_count >= self.config.retry_attempts:
                    break
                await asyncio.sleep(0.5)
    
    async def get_stream_info(self) -> dict:
        """Get RTSP stream information"""
        base_info = await super().get_stream_info()
        
        if self.cap and self._is_connected:
            # Get actual stream properties
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            base_info.update({
                "stream_type": "RTSP", 
                "actual_fps": actual_fps,
                "measured_fps": self._fps_actual,
                "actual_resolution": (actual_width, actual_height),
                "codec": self._get_codec_info(),
                "buffer_size": self.config.buffer_size
            })
        
        return base_info
    
    def _get_codec_info(self) -> str:
        """Get codec information"""
        if not self.cap:
            return "unknown"
        
        try:
            fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return codec.strip()
        except:
            return "unknown"

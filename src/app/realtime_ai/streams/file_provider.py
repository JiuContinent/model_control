"""
File Stream Provider for real-time AI recognition.

Handles local video files for testing and offline processing.
"""

import asyncio
import time
import os
from pathlib import Path
from typing import Optional, AsyncIterator
import cv2
import numpy as np
from loguru import logger

from ..core.base import BaseStreamProvider, StreamConfig, StreamProtocol
from ..core.exceptions import StreamConnectionException


class FileStreamProvider(BaseStreamProvider):
    """Local file stream provider using OpenCV"""
    
    def __init__(self, config: StreamConfig):
        super().__init__(config)
        self.cap: Optional[cv2.VideoCapture] = None
        self._last_frame_time = 0
        self._fps_actual = 0.0
        self._total_frames = 0
        self._target_fps = None
        self._loop_playback = False
        
        # Clean up file path
        self.file_path = self._clean_file_path(config.url)
        
        # Validate file exists
        if not os.path.exists(self.file_path):
            raise StreamConnectionException(
                f"Video file not found: {self.file_path}",
                stream_url=config.url
            )
    
    def _clean_file_path(self, url: str) -> str:
        """Clean and normalize file path"""
        # Remove file:// prefix if present
        if url.startswith('file://'):
            url = url[7:]
        
        # Convert to Path object for normalization
        path = Path(url)
        return str(path.resolve())
    
    async def connect(self) -> bool:
        """Open video file"""
        try:
            self.cap = cv2.VideoCapture(self.file_path)
            
            if not self.cap.isOpened():
                raise StreamConnectionException(
                    f"Failed to open video file: {self.file_path}",
                    stream_url=self.config.url
                )
            
            # Get file properties
            self._total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self._target_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            # Override FPS if specified in config
            if self.config.fps:
                self._target_fps = self.config.fps
            
            # Set resolution if specified
            if self.config.resolution:
                width, height = self.config.resolution
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Test read first frame
            ret, frame = self.cap.read()
            if not ret or frame is None:
                await self.disconnect()
                raise StreamConnectionException(
                    f"Failed to read first frame from video file: {self.file_path}",
                    stream_url=self.config.url
                )
            
            # Reset to beginning
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            
            self._is_connected = True
            self._last_frame_time = time.time()
            
            # Check for loop playback in additional params
            if (self.config.additional_params and 
                self.config.additional_params.get('loop', False)):
                self._loop_playback = True
            
            logger.info(f"Successfully opened video file: {self.file_path}")
            logger.info(f"File info - Frames: {self._total_frames}, FPS: {self._target_fps}")
            return True
            
        except Exception as e:
            await self.disconnect()
            if isinstance(e, StreamConnectionException):
                raise
            raise StreamConnectionException(
                f"Failed to open video file: {e}",
                stream_url=self.config.url
            )
    
    async def disconnect(self) -> None:
        """Close video file"""
        try:
            if self.cap:
                self.cap.release()
                self.cap = None
            self._is_connected = False
            logger.info(f"Closed video file: {self.file_path}")
        except Exception as e:
            logger.error(f"Error during file disconnect: {e}")
    
    async def get_frame(self) -> Optional[np.ndarray]:
        """Get next frame from video file"""
        if not self._is_connected or not self.cap:
            raise StreamConnectionException(
                "Video file not opened",
                stream_url=self.config.url
            )
        
        try:
            # Control playback speed to match target FPS
            if self._target_fps and self._last_frame_time > 0:
                expected_interval = 1.0 / self._target_fps
                current_time = time.time()
                time_since_last = current_time - self._last_frame_time
                
                if time_since_last < expected_interval:
                    sleep_time = expected_interval - time_since_last
                    await asyncio.sleep(sleep_time)
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            ret, frame = await loop.run_in_executor(None, self.cap.read)
            
            if not ret or frame is None:
                # End of file reached
                if self._loop_playback:
                    # Reset to beginning for loop playback
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = await loop.run_in_executor(None, self.cap.read)
                    
                    if ret and frame is not None:
                        logger.info(f"Looping video file: {self.file_path}")
                        self._frame_count += 1
                        self._last_frame_time = time.time()
                        return frame
                
                logger.info(f"Reached end of video file: {self.file_path}")
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
            logger.error(f"Error reading frame from file: {e}")
            return None
    
    async def get_frame_iterator(self) -> AsyncIterator[np.ndarray]:
        """Get async iterator for video file frames"""
        while self._is_connected:
            try:
                frame = await self.get_frame()
                if frame is not None:
                    yield frame
                else:
                    # End of file and not looping
                    if not self._loop_playback:
                        break
                    
            except Exception as e:
                logger.error(f"Error in file frame iterator: {e}")
                break
    
    async def get_stream_info(self) -> dict:
        """Get video file information"""
        base_info = await super().get_stream_info()
        
        if self.cap and self._is_connected:
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            
            base_info.update({
                "stream_type": "FILE",
                "file_path": self.file_path,
                "file_size_mb": os.path.getsize(self.file_path) / (1024 * 1024),
                "total_frames": self._total_frames,
                "current_frame": current_frame,
                "progress_percent": (current_frame / self._total_frames * 100) if self._total_frames > 0 else 0,
                "target_fps": self._target_fps,
                "measured_fps": self._fps_actual,
                "actual_resolution": (actual_width, actual_height),
                "codec": self._get_codec_info(),
                "loop_playback": self._loop_playback,
                "duration_seconds": self._total_frames / self._target_fps if self._target_fps > 0 else 0
            })
        
        return base_info
    
    def _get_codec_info(self) -> str:
        """Get video codec information"""
        if not self.cap:
            return "unknown"
        
        try:
            fourcc = int(self.cap.get(cv2.CAP_PROP_FOURCC))
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            return codec.strip()
        except:
            return "unknown"
    
    async def seek_to_frame(self, frame_number: int) -> bool:
        """Seek to specific frame number"""
        if not self._is_connected or not self.cap:
            return False
        
        try:
            if 0 <= frame_number < self._total_frames:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                return True
            return False
        except Exception as e:
            logger.error(f"Error seeking to frame {frame_number}: {e}")
            return False
    
    async def seek_to_time(self, time_seconds: float) -> bool:
        """Seek to specific time in seconds"""
        if not self._is_connected or not self.cap or not self._target_fps:
            return False
        
        frame_number = int(time_seconds * self._target_fps)
        return await self.seek_to_frame(frame_number)

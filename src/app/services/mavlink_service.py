import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from app.core.exceptions import MAVLinkException
from app.core.constants import MAVLINK_CONFIG
from app.models.mavlink_models import MavlinkMessage, MavlinkSession
from app.services.mqtt_service import mqtt_service
from app.mavlink.mavlink_receiver import mavlink_receiver


class MAVLinkService:
    """MAVLinkService"""
    
    def __init__(self):
        self.receiver = None
        self.is_running = False
        self.sessions: Dict[str, MavlinkSession] = {}
        self.messages: List[MavlinkMessage] = []
    
    async def start_receiver(self, host: str = None, port: int = None) -> Dict[str, Any]:
        """start_receiver MAVLink"""
        try:
            host = host or MAVLINK_CONFIG["default_host"]
            port = port or MAVLINK_CONFIG["default_port"]
            
            # Start MQTT service first
            try:
                await mqtt_service.start()
                logger.info("MQTT service started successfully")
            except Exception as mqtt_error:
                logger.warning(f"Failed to start MQTT service: {mqtt_error}")
            
            # Start the actual MAVLink receiver
            await mavlink_receiver.start(port)
            self.is_running = True
            
            logger.info(f"MAVLink receiver started successfully - {host}:{port}")
            return {
                "status": "started",
                "host": host,
                "port": port,
                "mqtt_status": mqtt_service.get_status(),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"MAVLink receiver start failed: {e}")
            raise MAVLinkException(f"Receiver start failed: {e}")
    
    async def stop_receiver(self) -> Dict[str, Any]:
        """Stop MAVLink receiver"""
        try:
            # Stop the actual MAVLink receiver
            await mavlink_receiver.stop()
            self.is_running = False
            
            # Stop MQTT service
            try:
                await mqtt_service.stop()
                logger.info("MQTT service stopped")
            except Exception as mqtt_error:
                logger.warning(f"Failed to stop MQTT service: {mqtt_error}")
            
            logger.info("MAVLink receiver stopped")
            return {
                "status": "stopped",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"MAVLink receiver stop failed: {e}")
            raise MAVLinkException(f"Receiver stop failed: {e}")
    
    async def get_receiver_status(self) -> Dict[str, Any]:
        """Get receiver status"""
        return {
            "is_running": mavlink_receiver.is_running(),
            "total_messages": mavlink_receiver.total_messages_received,
            "active_sessions": len(mavlink_receiver.sessions),
            "mqtt_status": mqtt_service.get_status(),
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get MAVLink messages"""
        try:
            messages = self.messages[-limit:] if limit > 0 else self.messages
            return [msg.dict() for msg in messages]
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            raise MAVLinkException(f"Failed to get messages: {e}")
    
    async def get_sessions(self) -> List[Dict[str, Any]]:
        """Get session information"""
        try:
            return [session.dict() for session in self.sessions.values()]
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            raise MAVLinkException(f"Failed to get sessions: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics"""
        try:
            if not self.messages:
                return {
                    "total_messages": 0,
                    "message_types": {},
                    "sessions_count": 0,
                    "last_message_time": None
                }
            
            # Count message types
            message_types = {}
            for msg in self.messages:
                msg_type = msg.message_type
                message_types[msg_type] = message_types.get(msg_type, 0) + 1
            
            return {
                "total_messages": len(self.messages),
                "message_types": message_types,
                "sessions_count": len(self.sessions),
                "last_message_time": self.messages[-1].timestamp.isoformat() if self.messages else None
            }
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            raise MAVLinkException(f"Failed to get statistics: {e}")


# Global MAVLink service instance
mavlink_service = MAVLinkService()

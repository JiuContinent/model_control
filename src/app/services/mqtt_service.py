"""
MQTT Service for publishing MAVLink data
"""
import json
import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime
import paho.mqtt.client as mqtt
from loguru import logger


class MQTTService:
    """MQTT service for publishing MAVLink data"""
    
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.is_connected = False
        self.is_running = False
        self.broker_host = "221.226.33.58"
        self.broker_port = 1883
        self.topic = "/ue/device/mavlink"
        self.client_id = f"mavlink_publisher_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Statistics
        self.messages_published = 0
        self.last_publish_time: Optional[datetime] = None
        
    async def start(self, broker_host: str = "27.11.11.30", broker_port: int = 1883, topic: str = "/ue/device/mavlink"):
        """Start MQTT service"""
        if self.is_running:
            logger.warning("MQTT service is already running")
            return
        
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        
        try:
            # Create MQTT client
            self.client = mqtt.Client(
                client_id=self.client_id,
                clean_session=True,
                protocol=mqtt.MQTTv311
            )
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            
            # Connect to broker
            logger.info(f"Connecting to MQTT broker: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Start network loop in a separate thread
            self.is_running = True
            threading.Thread(target=self._network_loop, daemon=True).start()
            
            # Wait for connection
            await asyncio.sleep(2)
            
            if self.is_connected:
                logger.info(f"MQTT service started successfully. Topic: {self.topic}")
            else:
                logger.error("Failed to connect to MQTT broker")
                raise Exception("MQTT connection failed")
                
        except Exception as e:
            logger.error(f"Failed to start MQTT service: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop MQTT service"""
        if not self.is_running:
            logger.warning("MQTT service is not running")
            return
        
        try:
            self.is_running = False
            
            if self.client:
                self.client.disconnect()
                self.client.loop_stop()
                self.client = None
            
            self.is_connected = False
            logger.info("MQTT service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping MQTT service: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            logger.info("Connected to MQTT broker successfully")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Return code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        self.messages_published += 1
        self.last_publish_time = datetime.now()
        logger.debug(f"Message published successfully. Message ID: {mid}")
    
    def _network_loop(self):
        """MQTT network loop in separate thread"""
        if self.client:
            self.client.loop_forever()
    
    async def publish_mavlink_data(self, mavlink_data: Dict[str, Any]):
        """Publish MAVLink data to MQTT topic"""
        if not self.is_connected or not self.client:
            logger.warning("MQTT client not connected")
            return False
        
        try:
            # Prepare message payload
            payload = {
                "timestamp": datetime.now().isoformat(),
                "mavlink_data": mavlink_data,
                "source": "model_control_system"
            }
            
            # Convert to JSON
            message = json.dumps(payload, ensure_ascii=False)
            
            # Publish message
            result = self.client.publish(self.topic, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"MQTT message queued for publishing: {self.topic}")
                return True
            else:
                logger.error(f"Failed to queue MQTT message. Return code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing MQTT message: {e}")
            return False
    
    async def publish_raw_packet(self, packet_data: bytes, client_addr: str):
        """Publish raw MAVLink packet data"""
        if not self.is_connected or not self.client:
            logger.warning("MQTT client not connected")
            return False
        
        try:
            # Prepare message payload
            payload = {
                "timestamp": datetime.now().isoformat(),
                "packet_data": packet_data.hex(),  # Convert bytes to hex string
                "client_address": client_addr,
                "packet_length": len(packet_data),
                "source": "model_control_system"
            }
            
            # Convert to JSON
            message = json.dumps(payload, ensure_ascii=False)
            
            # Publish message
            result = self.client.publish(self.topic, message, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Raw packet queued for MQTT publishing: {self.topic}")
                return True
            else:
                logger.error(f"Failed to queue raw packet. Return code: {result.rc}")
                return False
                
        except Exception as e:
            logger.error(f"Error publishing raw packet: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get MQTT service status"""
        return {
            "is_running": self.is_running,
            "is_connected": self.is_connected,
            "broker_host": self.broker_host,
            "broker_port": self.broker_port,
            "topic": self.topic,
            "client_id": self.client_id,
            "messages_published": self.messages_published,
            "last_publish_time": self.last_publish_time.isoformat() if self.last_publish_time else None
        }


# Global MQTT service instance
mqtt_service = MQTTService()

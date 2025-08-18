"""
MQTT API routes for managing MQTT service
"""
from fastapi import APIRouter, HTTPException
from typing import Optional

from app.services.mqtt_service import mqtt_service
from loguru import logger

router = APIRouter(prefix="/mqtt", tags=["MQTT"])


@router.post("/start")
async def start_mqtt_service(
    broker_host: Optional[str] = "221.226.33.58",
    broker_port: Optional[int] = 1883,
    topic: Optional[str] = "/ue/device/mavlink"
):
    """
    Start MQTT service
    
    Args:
        broker_host: MQTT broker host address
        broker_port: MQTT broker port
        topic: MQTT topic to publish to
        
    Returns:
        Start result
    """
    try:
        await mqtt_service.start(broker_host, broker_port, topic)
        return {
            "status": "started",
            "broker_host": broker_host,
            "broker_port": broker_port,
            "topic": topic,
            "mqtt_status": mqtt_service.get_status()
        }
    except Exception as e:
        logger.error(f"Failed to start MQTT service: {e}")
        raise HTTPException(status_code=500, detail=f"MQTT start failed: {e}")


@router.post("/stop")
async def stop_mqtt_service():
    """
    Stop MQTT service
    
    Returns:
        Stop result
    """
    try:
        await mqtt_service.stop()
        return {
            "status": "stopped",
            "mqtt_status": mqtt_service.get_status()
        }
    except Exception as e:
        logger.error(f"Failed to stop MQTT service: {e}")
        raise HTTPException(status_code=500, detail=f"MQTT stop failed: {e}")


@router.get("/status")
async def get_mqtt_status():
    """
    Get MQTT service status
    
    Returns:
        MQTT service status information
    """
    try:
        return mqtt_service.get_status()
    except Exception as e:
        logger.error(f"Failed to get MQTT status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MQTT status: {e}")


@router.post("/test-publish")
async def test_mqtt_publish(message: str = "Test message from Model Control System"):
    """
    Test MQTT publishing
    
    Args:
        message: Test message to publish
        
    Returns:
        Publish result
    """
    try:
        if not mqtt_service.is_connected:
            raise HTTPException(status_code=400, detail="MQTT service is not connected")
        
        # Create test payload
        test_data = {
            "message_id": 0,
            "system_id": 1,
            "component_id": 1,
            "sequence": 0,
            "payload": {"test": True, "message": message},
            "parsed_data": {"test_message": message},
            "is_valid": True
        }
        
        success = await mqtt_service.publish_mavlink_data(test_data)
        
        if success:
            return {
                "status": "published",
                "message": message,
                "topic": mqtt_service.topic
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to publish test message")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test MQTT publish: {e}")
        raise HTTPException(status_code=500, detail=f"Test publish failed: {e}")


@router.get("/health")
async def mqtt_health_check():
    """
    MQTT service health check
    
    Returns:
        Service health status
    """
    try:
        status = mqtt_service.get_status()
        return {
            "status": "healthy" if status["is_connected"] else "disconnected",
            "mqtt_connected": status["is_connected"],
            "broker_host": status["broker_host"],
            "topic": status["topic"],
            "messages_published": status["messages_published"]
        }
    except Exception as e:
        logger.error(f"MQTT health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

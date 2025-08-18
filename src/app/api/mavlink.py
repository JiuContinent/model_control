"""
MAVLink API routes - Using service layer for business logic
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.services.mavlink_service import mavlink_service
from app.core.exceptions import MAVLinkException
from loguru import logger

router = APIRouter(prefix="/mavlink", tags=["MAVLink"])


@router.post("/receiver/start")
async def start_receiver(host: Optional[str] = None, port: Optional[int] = None):
    """
    Start MAVLink receiver
    
    Args:
        host: Listening host address
        port: Listening port
        
    Returns:
        Start result
    """
    try:
        result = await mavlink_service.start_receiver(host, port)
        return result
    except MAVLinkException as e:
        logger.error(f"Failed to start receiver: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Receiver start exception: {e}")
        raise HTTPException(status_code=500, detail=f"Start failed: {e}")


@router.post("/receiver/stop")
async def stop_receiver():
    """
    Stop MAVLink receiver
    
    Returns:
        Stop result
    """
    try:
        result = await mavlink_service.stop_receiver()
        return result
    except MAVLinkException as e:
        logger.error(f"Failed to stop receiver: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Receiver stop exception: {e}")
        raise HTTPException(status_code=500, detail=f"Stop failed: {e}")


@router.get("/receiver/status")
async def get_receiver_status():
    """
    Get receiver status
    
    Returns:
        Receiver status information
    """
    try:
        return await mavlink_service.get_receiver_status()
    except Exception as e:
        logger.error(f"Failed to get receiver status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {e}")


@router.get("/messages")
async def get_messages(limit: int = Query(100, ge=1, le=1000)):
    """
    Get MAVLink messages
    
    Args:
        limit: Message count limit
        
    Returns:
        MAVLink message list
    """
    try:
        messages = await mavlink_service.get_messages(limit)
        return {
            "messages": messages,
            "total": len(messages),
            "limit": limit
        }
    except MAVLinkException as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Message get exception: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {e}")


@router.get("/sessions")
async def get_sessions():
    """
    Get session information
    
    Returns:
        Session list
    """
    try:
        sessions = await mavlink_service.get_sessions()
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
    except MAVLinkException as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Session get exception: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {e}")


@router.get("/statistics")
async def get_statistics():
    """
    Get statistics
    
    Returns:
        Statistics information
    """
    try:
        return await mavlink_service.get_statistics()
    except MAVLinkException as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Statistics get exception: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {e}")


@router.get("/health")
async def mavlink_health_check():
    """
    MAVLink service health check
    
    Returns:
        Service status
    """
    try:
        status = await mavlink_service.get_receiver_status()
        return {
            "status": "healthy" if status["is_running"] else "stopped",
            "receiver_running": status["is_running"],
            "total_messages": status["total_messages"],
            "active_sessions": status["active_sessions"]
        }
    except Exception as e:
        logger.error(f"MAVLink health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

"""
Dependency injection providers.
These functions are responsible for creating and providing various service instances required by API routes.
Using FastAPI's `Depends` system can easily manage and mock these dependencies, making testing easier.
"""

from app.services.ai_service import ai_service
from app.services.mavlink_service import mavlink_service


def get_ai_service():
    """Get AI service instance"""
    return ai_service


def get_mavlink_service():
    """Get MAVLink service instance"""
    return mavlink_service

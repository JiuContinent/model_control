"""
Simple MAVLink Models - Basic Pydantic models without Beanie
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MavlinkMessage(BaseModel):
    """Simple MAVLink message model"""
    message_id: int
    system_id: int
    component_id: int
    sequence: int
    payload: str  # Base64 encoded bytes
    timestamp: datetime
    client_address: str
    packet_length: int
    is_valid: bool = True
    version: int = 1


class MavlinkSession(BaseModel):
    """Simple MAVLink session model"""
    system_id: int
    client_address: str
    first_seen: datetime
    last_seen: datetime
    message_count: int = 0
    is_active: bool = True


class MavlinkStatistics(BaseModel):
    """Simple MAVLink statistics model"""
    date: str  # YYYY-MM-DD format
    total_messages: int = 0
    unique_systems: int = 0
    active_sessions: int = 0
    last_updated: datetime

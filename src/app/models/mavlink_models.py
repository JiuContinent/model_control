"""
MAVLink Data Models for MongoDB
Simplified models to avoid Pydantic field conflicts
"""
from beanie import Document, Indexed
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone, date


class MavlinkMessage(Document):
    """MAVLink message model"""
    
    message_id: int = Indexed()
    system_id: int = Indexed()
    component_id: int
    sequence: int
    payload: bytes
    parsed_data: str = Field(default="{}")  # JSON string instead of Dict
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    client_address: str
    packet_length: int
    is_valid: bool = True
    version: int = 1  # MAVLink version (1 or 2)
    
    class Settings:
        name = "mavlink_messages"
        indexes = [
            "message_id",
            "system_id", 
            "timestamp",
            "client_address"
        ]


class MavlinkSession(Document):
    """MAVLink session tracking model"""
    
    system_id: int = Indexed()
    client_address: str = Indexed()
    first_seen: datetime
    last_seen: datetime
    message_count: int = 0
    is_active: bool = True
    last_message_id: Optional[int] = None
    session_duration: Optional[float] = None  # in seconds
    
    class Settings:
        name = "mavlink_sessions"
        indexes = [
            "system_id",
            "client_address",
            "is_active",
            "last_seen"
        ]


class MavlinkStatistics(Document):
    """Daily MAVLink statistics model"""
    
    stat_date: date = Indexed()
    total_messages: int = 0
    unique_systems: int = 0
    active_sessions: int = 0
    last_updated: datetime
    message_type_counts_json: str = Field(default="{}")  # JSON string instead of Dict
    system_message_counts_json: str = Field(default="{}")  # JSON string instead of Dict
    
    class Settings:
        name = "mavlink_statistics"
        indexes = [
            "stat_date",
            "total_messages"
        ]


class MavlinkSystemInfo(Document):
    """MAVLink system information model"""
    
    system_id: int = Indexed()
    component_id: int
    autopilot_type: Optional[int] = None
    vehicle_type: Optional[int] = None
    first_seen: datetime
    last_seen: datetime
    total_messages: int = 0
    message_type_list_json: str = Field(default="[]")  # JSON string instead of List
    is_active: bool = True
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    
    class Settings:
        name = "mavlink_system_info"
        indexes = [
            "system_id",
            "component_id",
            "is_active"
        ]


class MavlinkErrorLog(Document):
    """MAVLink error logging model"""
    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    error_type: str  # "parsing_error", "crc_mismatch", "invalid_packet", etc.
    error_message: str
    packet_data: Optional[bytes] = None
    client_address: Optional[str] = None
    system_id: Optional[int] = None
    severity: str = "warning"  # "info", "warning", "error", "critical"
    
    class Settings:
        name = "mavlink_error_logs"
        indexes = [
            "timestamp",
            "error_type",
            "severity",
            "system_id"
        ]

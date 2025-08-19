"""
Device Manager for tracking multiple MAVLink devices
"""
import time
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, asdict


@dataclass
class DeviceInfo:
    """Device information"""
    device_id: str
    system_id: int
    component_id: int
    client_address: str
    device_type: str = "unknown"
    first_seen: datetime = None
    last_seen: datetime = None
    message_count: int = 0
    gps_fix_count: int = 0
    last_position: Optional[Dict[str, float]] = None
    last_altitude: float = 0.0
    last_fix_type: int = 0
    last_satellites: int = 0
    
    def __post_init__(self):
        if self.first_seen is None:
            self.first_seen = datetime.now(timezone.utc)
        if self.last_seen is None:
            self.last_seen = datetime.now(timezone.utc)


class DeviceManager:
    """Manager for tracking multiple MAVLink devices"""
    
    def __init__(self):
        self.devices: Dict[str, DeviceInfo] = {}
        self.device_counter = 0
    
    def get_or_create_device(self, system_id: int, component_id: int, client_address: str) -> DeviceInfo:
        """Get existing device or create new one"""
        device_id = f"device_{system_id}_{component_id}_{client_address.replace('.', '_').replace(':', '_')}"
        
        if device_id not in self.devices:
            self.device_counter += 1
            device = DeviceInfo(
                device_id=device_id,
                system_id=system_id,
                component_id=component_id,
                client_address=client_address
            )
            self.devices[device_id] = device
            print(f"[DEVICE] New device registered: {device_id}")
        
        return self.devices[device_id]
    
    def update_device_gps(self, device_id: str, gps_data: Dict[str, Any]):
        """Update device with GPS data"""
        if device_id in self.devices:
            device = self.devices[device_id]
            device.last_seen = datetime.now(timezone.utc)
            device.message_count += 1
            device.gps_fix_count += 1
            
            # Update position data
            device.last_position = {
                "latitude": gps_data.get("latitude", 0.0),
                "longitude": gps_data.get("longitude", 0.0)
            }
            device.last_altitude = gps_data.get("altitude", 0.0)
            device.last_fix_type = gps_data.get("fix_type", 0)
            device.last_satellites = gps_data.get("satellites_visible", 0)
    
    def get_device_info(self, device_id: str) -> Optional[DeviceInfo]:
        """Get device information"""
        return self.devices.get(device_id)
    
    def get_all_devices(self) -> Dict[str, DeviceInfo]:
        """Get all devices"""
        return self.devices.copy()
    
    def get_active_devices(self, timeout_seconds: int = 300) -> Dict[str, DeviceInfo]:
        """Get devices that have been active in the last timeout_seconds"""
        now = datetime.now(timezone.utc)
        active_devices = {}
        
        for device_id, device in self.devices.items():
            if (now - device.last_seen).total_seconds() < timeout_seconds:
                active_devices[device_id] = device
        
        return active_devices
    
    def get_device_stats(self) -> Dict[str, Any]:
        """Get device statistics"""
        total_devices = len(self.devices)
        active_devices = len(self.get_active_devices())
        
        total_messages = sum(device.message_count for device in self.devices.values())
        total_gps_fixes = sum(device.gps_fix_count for device in self.devices.values())
        
        return {
            "total_devices": total_devices,
            "active_devices": active_devices,
            "total_messages": total_messages,
            "total_gps_fixes": total_gps_fixes,
            "device_counter": self.device_counter
        }
    
    def cleanup_old_devices(self, timeout_seconds: int = 3600):
        """Remove devices that haven't been seen for a long time"""
        now = datetime.now(timezone.utc)
        devices_to_remove = []
        
        for device_id, device in self.devices.items():
            if (now - device.last_seen).total_seconds() > timeout_seconds:
                devices_to_remove.append(device_id)
        
        for device_id in devices_to_remove:
            del self.devices[device_id]
            print(f"[DEVICE] Removed inactive device: {device_id}")
    
    def export_device_data(self) -> Dict[str, Any]:
        """Export all device data for MQTT or API"""
        devices_data = {}
        for device_id, device in self.devices.items():
            device_dict = {
                "device_id": device.device_id,
                "system_id": device.system_id,
                "component_id": device.component_id,
                "client_address": device.client_address,
                "device_type": device.device_type,
                "first_seen": device.first_seen.isoformat(),
                "last_seen": device.last_seen.isoformat(),
                "message_count": device.message_count,
                "gps_fix_count": device.gps_fix_count,
                "last_position": device.last_position,
                "last_altitude": device.last_altitude,
                "last_fix_type": device.last_fix_type,
                "last_satellites": device.last_satellites
            }
            devices_data[device_id] = device_dict
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "device_count": len(self.devices),
            "devices": devices_data,
            "stats": self.get_device_stats()
        }


# Global device manager instance
device_manager = DeviceManager()

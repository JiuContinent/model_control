"""
MAVLink Protocol Parser
Parses MAVLink binary data packets
"""
import struct
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timezone


class MavlinkParser:
    """MAVLink protocol parser"""
    
    # MAVLink protocol constants
    MAVLINK_STX = 0xFD  # MAVLink v2 start byte
    MAVLINK_V1_STX = 0xFE  # MAVLink v1 start byte
    
    def __init__(self):
        self.message_definitions = self._init_message_definitions()
    
    def _init_message_definitions(self) -> Dict[int, Dict[str, Any]]:
        """Initialize message definitions"""
        return {
            # Heartbeat message
            0: {
                "name": "HEARTBEAT",
                "fields": [
                    ("type", "uint8"),
                    ("autopilot", "uint8"), 
                    ("base_mode", "uint8"),
                    ("custom_mode", "uint32"),
                    ("system_status", "uint8"),
                    ("mavlink_version", "uint8")
                ]
            },
            # System status message
            1: {
                "name": "SYS_STATUS",
                "fields": [
                    ("voltage_battery", "uint16"),
                    ("current_battery", "int16"),
                    ("battery_remaining", "int8"),
                    ("drop_rate_comm", "uint16"),
                    ("errors_comm", "uint16"),
                    ("errors_count1", "uint16"),
                    ("errors_count2", "uint16"),
                    ("errors_count3", "uint16"),
                    ("errors_count4", "uint16")
                ]
            },
            # Attitude message (message ID 30)
            30: {
                "name": "ATTITUDE",
                "fields": [
                    ("time_boot_ms", "uint32"),
                    ("roll", "float"),
                    ("pitch", "float"),
                    ("yaw", "float"),
                    ("rollspeed", "float"),
                    ("pitchspeed", "float"),
                    ("yawspeed", "float")
                ]
            },
            # Scaled pressure message (message ID 29)
            29: {
                "name": "SCALED_PRESSURE",
                "fields": [
                    ("time_boot_ms", "uint32"),
                    ("press_abs", "float"),
                    ("press_diff", "float"),
                    ("temperature", "int16")
                ]
            },
            # VFR HUD message (message ID 74)
            74: {
                "name": "VFR_HUD",
                "fields": [
                    ("airspeed", "float"),
                    ("groundspeed", "float"),
                    ("heading", "int16"),
                    ("throttle", "uint16"),
                    ("alt", "float"),
                    ("climb", "float")
                ]
            }
        }
    
    def parse_packet(self, data: bytes, source_ip: str = None, source_port: int = None) -> Optional[Dict[str, Any]]:
        """Parse MAVLink data packet"""
        try:
            if len(data) < 10:  # Minimum packet length check
                return None
            
            # Check start byte
            if data[0] not in [self.MAVLINK_STX, self.MAVLINK_V1_STX]:
                return None
            
            # Parse packet header
            if data[0] == self.MAVLINK_STX:  # MAVLink v2
                return self._parse_v2_packet(data, source_ip, source_port)
            else:  # MAVLink v1
                return self._parse_v1_packet(data, source_ip, source_port)
                
        except Exception as e:
            print(f"Error parsing MAVLink packet: {e}")
            return None
    
    def _parse_v2_packet(self, data: bytes, source_ip: str, source_port: int) -> Optional[Dict[str, Any]]:
        """Parse MAVLink v2 packet"""
        try:
            # MAVLink v2 header format: [STX][LEN][INCOMPAT][COMPAT][SEQ][SYSID][COMPID][MSGID][PAYLOAD...][SIG...][CRC]
            if len(data) < 10:
                return None
            
            payload_length = data[1]
            incompat_flags = data[2]
            compat_flags = data[3]
            sequence = data[4]
            system_id = data[5]
            component_id = data[6]
            message_id = struct.unpack('<I', data[7:11])[0]
            
            # Calculate payload start position
            payload_start = 11
            payload_end = payload_start + payload_length
            
            if len(data) < payload_end + 2:  # +2 for CRC
                return None
            
            payload = data[payload_start:payload_end]
            crc_data = data[payload_end:payload_end + 2]
            crc = struct.unpack('<H', crc_data)[0]
            
            # Verify CRC
            calculated_crc = self._calculate_crc(data[:payload_end])
            is_valid = calculated_crc == crc
            
            # Parse payload if message definition exists
            parsed_data = {}
            if message_id in self.message_definitions:
                parsed_data = self._parse_payload(payload, message_id)
            
            return {
                "version": 2,
                "message_id": message_id,
                "system_id": system_id,
                "component_id": component_id,
                "sequence": sequence,
                "payload": payload,
                "payload_length": payload_length,
                "incompat_flags": incompat_flags,
                "compat_flags": compat_flags,
                "crc": crc,
                "calculated_crc": calculated_crc,
                "is_valid": is_valid,
                "parsed_data": parsed_data,
                "source_ip": source_ip,
                "source_port": source_port
            }
            
        except Exception as e:
            print(f"Error parsing MAVLink v2 packet: {e}")
            return None
    
    def _parse_v1_packet(self, data: bytes, source_ip: str, source_port: int) -> Optional[Dict[str, Any]]:
        """Parse MAVLink v1 packet"""
        try:
            # MAVLink v1 header format: [STX][LEN][SEQ][SYSID][COMPID][MSGID][PAYLOAD...][CRC]
            if len(data) < 8:
                return None
            
            payload_length = data[1]
            sequence = data[2]
            system_id = data[3]
            component_id = data[4]
            message_id = data[5]
            
            # Calculate payload start position
            payload_start = 6
            payload_end = payload_start + payload_length
            
            if len(data) < payload_end + 2:  # +2 for CRC
                return None
            
            payload = data[payload_start:payload_end]
            crc_data = data[payload_end:payload_end + 2]
            crc = struct.unpack('<H', crc_data)[0]
            
            # Verify CRC
            calculated_crc = self._calculate_crc(data[:payload_end])
            is_valid = calculated_crc == crc
            
            # Parse payload if message definition exists
            parsed_data = {}
            if message_id in self.message_definitions:
                parsed_data = self._parse_payload(payload, message_id)
            
            return {
                "version": 1,
                "message_id": message_id,
                "system_id": system_id,
                "component_id": component_id,
                "sequence": sequence,
                "payload": payload,
                "payload_length": payload_length,
                "crc": crc,
                "calculated_crc": calculated_crc,
                "is_valid": is_valid,
                "parsed_data": parsed_data,
                "source_ip": source_ip,
                "source_port": source_port
            }
            
        except Exception as e:
            print(f"Error parsing MAVLink v1 packet: {e}")
            return None
    
    def _parse_payload(self, payload: bytes, message_id: int) -> Dict[str, Any]:
        """Parse payload based on message definition"""
        try:
            if message_id not in self.message_definitions:
                return {}
            
            definition = self.message_definitions[message_id]
            fields = definition["fields"]
            parsed = {}
            
            offset = 0
            for field_name, field_type in fields:
                try:
                    if field_type == "uint8":
                        value = payload[offset]
                        offset += 1
                    elif field_type == "int8":
                        value = struct.unpack('<b', payload[offset:offset+1])[0]
                        offset += 1
                    elif field_type == "uint16":
                        value = struct.unpack('<H', payload[offset:offset+2])[0]
                        offset += 2
                    elif field_type == "int16":
                        value = struct.unpack('<h', payload[offset:offset+2])[0]
                        offset += 2
                    elif field_type == "uint32":
                        value = struct.unpack('<I', payload[offset:offset+4])[0]
                        offset += 4
                    elif field_type == "int32":
                        value = struct.unpack('<i', payload[offset:offset+4])[0]
                        offset += 4
                    elif field_type == "float":
                        value = struct.unpack('<f', payload[offset:offset+4])[0]
                        offset += 4
                    elif field_type == "double":
                        value = struct.unpack('<d', payload[offset:offset+8])[0]
                        offset += 8
                    else:
                        value = None
                        offset += 1
                    
                    parsed[field_name] = value
                    
                except (IndexError, struct.error):
                    parsed[field_name] = None
                    break
            
            return parsed
            
        except Exception as e:
            print(f"Error parsing payload: {e}")
            return {}
    
    def _calculate_crc(self, data: bytes) -> int:
        """Calculate MAVLink CRC"""
        try:
            # MAVLink CRC calculation
            crc = 0xFFFF
            
            for byte in data:
                crc ^= byte << 8
                for _ in range(8):
                    if crc & 0x8000:
                        crc = (crc << 1) ^ 0x1021
                    else:
                        crc = crc << 1
                    crc &= 0xFFFF
            
            return crc
            
        except Exception as e:
            print(f"Error calculating CRC: {e}")
            return 0
    
    def get_message_name(self, message_id: int) -> str:
        """Get message name by ID"""
        if message_id in self.message_definitions:
            return self.message_definitions[message_id]["name"]
        return f"UNKNOWN_{message_id}"
    
    def add_message_definition(self, message_id: int, name: str, fields: list):
        """Add custom message definition"""
        self.message_definitions[message_id] = {
            "name": name,
            "fields": fields
        }

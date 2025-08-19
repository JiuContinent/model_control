"""
Simple MAVLink Parser - Basic binary data parsing
"""
import struct
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class SimpleMavlinkParser:
    """Simple MAVLink packet parser"""
    
    # MAVLink message type mappings
    MESSAGE_TYPES = {
        0: "HEARTBEAT",
        1: "SYS_STATUS", 
        2: "SYSTEM_TIME",
        29: "SCALED_PRESSURE",
        30: "ATTITUDE",
        33: "GLOBAL_POSITION_INT",
        74: "VFR_HUD",
        93: "MEMINFO",
        105: "SYS_STATUS",
        115: "POWER_STATUS",
        116: "MEMINFO",
        117: "RAW_IMU",
        118: "SCALED_IMU",
        119: "SCALED_IMU2",
        120: "SCALED_IMU3",
        121: "VIBRATION",
        122: "MISSION_CURRENT",
        147: "BATTERY_STATUS",
        161: "SERVO_OUTPUT_RAW",
        193: "EKF_STATUS_REPORT",
        241: "VIBRATION"
    }
    
    def __init__(self):
        self.packet_count = 0
        self.sample_rate_counter = 0
        self.sample_rate_interval = 10  # 每10个包输出一次
    
    def parse_packet(self, data: bytes, client_address: str = "unknown") -> Optional[Dict[str, Any]]:
        """Parse MAVLink packet and return basic info"""
        try:
            if len(data) < 8:  # Minimum packet size
                return None
            
            # Check for MAVLink v2 signature
            if data[0] == 0xFD:  # MAVLink v2
                return self._parse_v2_packet(data, client_address)
            else:
                return None
            
        except Exception as e:
            print(f"Error parsing packet: {e}")
            return None
    
    def _parse_v2_packet(self, data: bytes, client_address: str) -> Optional[Dict[str, Any]]:
        """Parse MAVLink v2 packet"""
        try:
            if len(data) < 10:
                return None
            
            if data[0] != 0xFD:
                return None
            
            # MAVLink v2 header: [FD][LEN][INCOMPAT][COMPAT][SEQ][SYSID][COMPID][MSGID(3)][PAYLOAD...][CRC][SIGNATURE?]
            payload_length = data[1]
            incompat_flags = data[2]
            compat_flags = data[3]
            sequence = data[4]
            system_id = data[5]
            component_id = data[6]
            
            # 24-bit little-endian message id
            message_id = data[7] | (data[8] << 8) | (data[9] << 16)
            
            payload_start = 10
            payload_end = payload_start + payload_length
            
            # Ensure payload present (ignore CRC/signature)
            if len(data) < payload_end:
                return None
            
            payload = data[payload_start:payload_end]
            
            message_type = self.MESSAGE_TYPES.get(message_id, f"UNKNOWN_{message_id}")
            
            message = {
                "message_id": message_id,
                "message_type": message_type,
                "system_id": system_id,
                "component_id": component_id,
                "sequence": sequence,
                "payload": payload,
                "payload_length": payload_length,
                "timestamp": datetime.now(timezone.utc),
                "client_address": client_address,
                "packet_length": len(data),
                "is_valid": True,
                "version": 2
            }
            
            self.packet_count += 1
            self.sample_rate_counter += 1
            if self.sample_rate_counter >= self.sample_rate_interval:
                self._print_formatted_message(message, data)
                self.sample_rate_counter = 0
            
            return message
        except Exception as e:
            print(f"Error parsing v2 packet: {e}")
            return None
    
    def _print_formatted_message(self, message: Dict[str, Any], raw_data: bytes):
        """Print formatted message like expected output"""
        try:
            # Convert raw data to hex
            hex_data = raw_data.hex()
            
            # Get current time
            now = datetime.now()
            time_str = now.strftime("[%H:%M:%S.%f")[:-3] + "]"
            
            # Format output
            print(f"{time_str} Received {len(raw_data)} bytes UDP data (sample rate: 1/{self.sample_rate_interval}):")
            print(f"  Raw data (hex): {hex_data}")
            print(f"  Parsed MAVLink message: System ID={message['system_id']}, Type={message['message_type']}")
            
            # Add equipment status (placeholder)
            print(f"    Equipment-{message['system_id']}: Position(0.000000, 0.000000) Altitude 0.0m Battery 100%")
            print()
            
        except Exception as e:
            print(f"Error formatting message: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parser statistics"""
        return {
            "packets_parsed": self.packet_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

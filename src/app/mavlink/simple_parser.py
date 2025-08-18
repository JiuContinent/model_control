"""
Simple MAVLink Parser - Basic binary data parsing
"""
import struct
import base64
from datetime import datetime, timezone
from typing import Optional, Dict, Any


class SimpleMavlinkParser:
    """Simple MAVLink packet parser"""
    
    def __init__(self):
        self.packet_count = 0
    
    def parse_packet(self, data: bytes, client_address: str = "unknown") -> Optional[Dict[str, Any]]:
        """Parse MAVLink packet and return basic info"""
        try:
            if len(data) < 8:  # Minimum packet size
                return None
            
            # Basic packet structure (MAVLink v1)
            # FD + length + sequence + system_id + component_id + message_id + payload + CRC
            if data[0] == 0xFD:  # MAVLink v2 signature
                version = 2
                if len(data) < 10:
                    return None
                length = data[1]
                sequence = data[2]
                system_id = data[3]
                component_id = data[4]
                message_id = struct.unpack('<H', data[5:7])[0]  # 16-bit message ID
                payload_start = 7
            else:
                return None
            
            # Extract payload
            payload_end = payload_start + length
            if payload_end > len(data):
                return None
            
            payload = data[payload_start:payload_end]
            payload_b64 = base64.b64encode(payload).decode('utf-8')
            
            # Create message object
            message = {
                "message_id": message_id,
                "system_id": system_id,
                "component_id": component_id,
                "sequence": sequence,
                "payload": payload_b64,
                "timestamp": datetime.now(timezone.utc),
                "client_address": client_address,
                "packet_length": len(data),
                "is_valid": True,
                "version": version
            }
            
            self.packet_count += 1
            return message
            
        except Exception as e:
            print(f"Error parsing packet: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get parser statistics"""
        return {
            "packets_parsed": self.packet_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

#!/usr/bin/env python3
"""
Debug GPS_RAW_INT message parsing
"""
import struct

def debug_gps_payload():
    """Debug GPS payload parsing"""
    # GPS payload from your data
    payload_hex = "40da8bef000000009e781a13fa59f8460cf3000053005e000a0026730414d4ff0000d20e0000e8120000ab02"
    payload = bytes.fromhex(payload_hex)
    
    print(f"GPS payload (hex): {payload_hex}")
    print(f"Payload length: {len(payload)} bytes")
    
    # Try different parsing approaches
    print("\n=== Manual parsing ===")
    
    # Parse first few fields manually
    if len(payload) >= 8:
        time_usec = struct.unpack('<Q', payload[0:8])[0]
        print(f"time_usec: {time_usec}")
    
    if len(payload) >= 9:
        fix_type = payload[8]
        print(f"fix_type: {fix_type}")
    
    if len(payload) >= 13:
        lat = struct.unpack('<i', payload[9:13])[0]
        print(f"lat (raw): {lat}")
        print(f"lat (degrees): {lat / 1e7}")
    
    if len(payload) >= 17:
        lon = struct.unpack('<i', payload[13:17])[0]
        print(f"lon (raw): {lon}")
        print(f"lon (degrees): {lon / 1e7}")
    
    if len(payload) >= 21:
        alt = struct.unpack('<i', payload[17:21])[0]
        print(f"alt (raw): {alt}")
        print(f"alt (meters): {alt / 1000.0}")
    
    print("\n=== Expected values ===")
    print("Expected lat: 32.050192")
    print("Expected lon: 119.068108")
    print("Expected alt: 62.2")

if __name__ == "__main__":
    debug_gps_payload()

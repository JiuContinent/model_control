#!/usr/bin/env python3
"""
Test script for GPS_RAW_INT message parsing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.advanced_parser import AdvancedMavlinkParser

def test_gps_raw_int():
    """Test GPS_RAW_INT message parsing"""
    parser = AdvancedMavlinkParser()
    
    # Your test data
    test_data_hex = "fd2c000090090118000040da8bef000000009e781a13fa59f8460cf3000053005e000a0026730414d4ff0000d20e0000e8120000ab029bc0"
    test_data = bytes.fromhex(test_data_hex)
    
    print(f"Testing GPS_RAW_INT parsing with data: {test_data_hex}")
    print(f"Data length: {len(test_data)} bytes")
    
    # Parse the packet
    result = parser.parse_packet(test_data, "test_client")
    
    if result:
        print(f"\nParsed result:")
        print(f"  Message ID: {result['message_id']}")
        print(f"  Message Type: {result['message_type']}")
        print(f"  System ID: {result['system_id']}")
        print(f"  Component ID: {result['component_id']}")
        print(f"  Payload length: {result['payload_length']}")
        print(f"  Actual payload length: {result['actual_payload_length']}")
        print(f"  Is truncated: {result['is_truncated']}")
        
        if 'parsed_data' in result:
            parsed = result['parsed_data']
            print(f"\nParsed GPS data:")
            for key, value in parsed.items():
                print(f"  {key}: {value}")
            
            # Check if we have position data
            if 'lat' in parsed and 'lon' in parsed:
                lat = parsed['lat']
                lon = parsed['lon']
                alt = parsed.get('alt', 0.0)
                print(f"\nPosition: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
    else:
        print("Failed to parse packet")

if __name__ == "__main__":
    test_gps_raw_int()

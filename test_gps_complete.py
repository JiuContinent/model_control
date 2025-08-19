#!/usr/bin/env python3
"""
Test script for complete GPS_RAW_INT message parsing
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.advanced_parser import AdvancedMavlinkParser

def test_complete_gps_data():
    """Test complete GPS_RAW_INT message parsing"""
    parser = AdvancedMavlinkParser()
    
    # Complete GPS data (62 bytes)
    complete_data_hex = "fd2c000090090118000040da8bef000000009e781a13fa59f8460cf3000053005e000a0026730414d4ff0000d20e0000e8120000ab029bc0"
    complete_data = bytes.fromhex(complete_data_hex)
    
    print(f"Testing complete GPS_RAW_INT parsing with data: {complete_data_hex}")
    print(f"Data length: {len(complete_data)} bytes")
    
    # Parse the packet
    result = parser.parse_packet(complete_data, "test_client")
    
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

def test_truncated_data():
    """Test truncated data parsing"""
    parser = AdvancedMavlinkParser()
    
    # Truncated data (37 bytes)
    truncated_data_hex = "fdc000000180000d8bf000009e8113a5f860f300530500a02630144f000d0e00e82000b09b"
    truncated_data = bytes.fromhex(truncated_data_hex)
    
    print(f"\nTesting truncated data parsing with data: {truncated_data_hex}")
    print(f"Data length: {len(truncated_data)} bytes")
    
    # Parse the packet
    result = parser.parse_packet(truncated_data, "test_client")
    
    if result:
        print(f"\nParsed result:")
        print(f"  Message ID: {result['message_id']}")
        print(f"  Message Type: {result['message_type']}")
        print(f"  System ID: {result['system_id']}")
        print(f"  Component ID: {result['component_id']}")
        print(f"  Payload length: {result['payload_length']}")
        print(f"  Actual payload length: {result['actual_payload_length']}")
        print(f"  Is truncated: {result['is_truncated']}")
        
        # Show raw payload for debugging
        if 'payload' in result:
            print(f"  Raw payload (hex): {result['payload'].hex()}")
    else:
        print("Failed to parse packet")

if __name__ == "__main__":
    test_complete_gps_data()
    test_truncated_data()

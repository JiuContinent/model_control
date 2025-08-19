#!/usr/bin/env python3
"""
Test script for GPS parsing only (without MQTT)
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.advanced_parser import AdvancedMavlinkParser

def test_gps_parsing():
    """Test GPS parsing functionality"""
    print("Testing GPS parsing functionality...")
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Test GPS data from your logs
    test_data_hex = "fd2c00000109011800006088a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005501"
    test_data = bytes.fromhex(test_data_hex)
    
    print(f"Testing with GPS data: {test_data_hex}")
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
        
        if result['message_type'] == 'GPS_RAW_INT':
            parsed_data = result.get('parsed_data', {})
            print(f"\nParsed GPS data:")
            for key, value in parsed_data.items():
                print(f"  {key}: {value}")
            
            if 'lat' in parsed_data and 'lon' in parsed_data:
                lat = parsed_data['lat']
                lon = parsed_data['lon']
                alt = parsed_data.get('alt', 0.0)
                print(f"\nGPS Position: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
                
                # Test the MQTT data format that would be sent
                gps_data = {
                    "system_id": result['system_id'],
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": alt,
                    "timestamp": "2025-08-19T15:56:43.407Z",
                    "fix_type": parsed_data.get('fix_type', 0),
                    "satellites_visible": parsed_data.get('satellites_visible', 0),
                    "ground_speed": parsed_data.get('vel', 0.0),
                    "course_over_ground": parsed_data.get('cog', 0.0),
                    "raw_data": parsed_data
                }
                
                print(f"\nMQTT GPS data format:")
                import json
                print(json.dumps(gps_data, indent=2, ensure_ascii=False))
            else:
                print("No valid GPS position data found")
        else:
            print(f"Not a GPS message: {result['message_type']}")
    else:
        print("Failed to parse packet")

if __name__ == "__main__":
    test_gps_parsing()

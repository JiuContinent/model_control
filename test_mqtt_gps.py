#!/usr/bin/env python3
"""
Test script for MQTT GPS data publishing
"""
import sys
import os
import asyncio
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.services.mqtt_service import mqtt_service
from app.mavlink.advanced_parser import AdvancedMavlinkParser

async def test_mqtt_gps_publishing():
    """Test MQTT GPS data publishing"""
    print("Testing MQTT GPS data publishing...")
    
    # Start MQTT service
    try:
        await mqtt_service.start()
        print("MQTT service started successfully")
    except Exception as e:
        print(f"Failed to start MQTT service: {e}")
        return
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Test GPS data
    test_data_hex = "fd2c00000109011800006088a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005501"
    test_data = bytes.fromhex(test_data_hex)
    
    print(f"Testing with GPS data: {test_data_hex}")
    print(f"Data length: {len(test_data)} bytes")
    
    # Parse the packet
    result = parser.parse_packet(test_data, "test_client")
    
    if result:
        print(f"Parsed result:")
        print(f"  Message ID: {result['message_id']}")
        print(f"  Message Type: {result['message_type']}")
        print(f"  System ID: {result['system_id']}")
        
        if result['message_type'] == 'GPS_RAW_INT':
            parsed_data = result.get('parsed_data', {})
            if 'lat' in parsed_data and 'lon' in parsed_data:
                lat = parsed_data['lat']
                lon = parsed_data['lon']
                alt = parsed_data.get('alt', 0.0)
                print(f"GPS Position: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
                
                # Test MQTT publishing
                print("Publishing GPS data to MQTT...")
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
                
                success = await mqtt_service.publish_gps_data(gps_data)
                if success:
                    print("GPS data published to MQTT successfully!")
                else:
                    print("Failed to publish GPS data to MQTT")
            else:
                print("No valid GPS position data found")
        else:
            print(f"Not a GPS message: {result['message_type']}")
    else:
        print("Failed to parse packet")
    
    # Wait a bit for MQTT to process
    await asyncio.sleep(2)
    
    # Stop MQTT service
    await mqtt_service.stop()
    print("MQTT service stopped")

if __name__ == "__main__":
    asyncio.run(test_mqtt_gps_publishing())

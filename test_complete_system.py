#!/usr/bin/env python3
"""
Complete system test for GPS parsing and MQTT publishing
"""
import sys
import os
import asyncio
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.services.mqtt_service import mqtt_service
from app.mavlink.advanced_parser import AdvancedMavlinkParser

async def test_complete_system():
    """Test complete GPS parsing and MQTT publishing system"""
    print("=== Complete System Test ===")
    print("Testing GPS parsing and MQTT publishing...")
    
    # Start MQTT service
    try:
        await mqtt_service.start()
        print("MQTT service started")
    except Exception as e:
        print(f"MQTT service start error: {e}")
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Test multiple GPS data packets
    test_data_list = [
        "fd2c00000109011800006088a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005501",
        "fd2c00000209011800006188a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005502",
        "fd2c00000309011800006288a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005503"
    ]
    
    for i, test_data_hex in enumerate(test_data_list):
        print(f"\n--- Test {i+1} ---")
        test_data = bytes.fromhex(test_data_hex)
        
        # Parse the packet
        result = parser.parse_packet(test_data, f"test_client_{i}")
        
        if result and result['message_type'] == 'GPS_RAW_INT':
            parsed_data = result.get('parsed_data', {})
            if 'lat' in parsed_data and 'lon' in parsed_data:
                lat = parsed_data['lat']
                lon = parsed_data['lon']
                alt = parsed_data.get('alt', 0.0)
                
                print(f"GPS Position: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
                
                # Test MQTT publishing
                gps_data = {
                    "system_id": result['system_id'],
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": alt,
                    "timestamp": "2025-08-19T16:00:00.000Z",
                    "fix_type": parsed_data.get('fix_type', 0),
                    "satellites_visible": parsed_data.get('satellites_visible', 0),
                    "ground_speed": parsed_data.get('vel', 0.0),
                    "course_over_ground": parsed_data.get('cog', 0.0),
                    "raw_data": parsed_data
                }
                
                success = await mqtt_service.publish_gps_data(gps_data)
                if success:
                    print("? GPS data published to MQTT successfully!")
                else:
                    print("? Failed to publish GPS data to MQTT")
            else:
                print("? No valid GPS position data found")
        else:
            print(f"? Not a GPS message: {result['message_type'] if result else 'Parse failed'}")
        
        # Wait between tests
        await asyncio.sleep(1)
    
    # Show MQTT status
    print(f"\n=== MQTT Status ===")
    status = mqtt_service.get_status()
    print(f"Running: {status['is_running']}")
    print(f"Connected: {status['is_connected']}")
    print(f"Broker: {status['broker_host']}:{status['broker_port']}")
    print(f"Messages published: {status['messages_published']}")
    
    # Stop MQTT service
    await mqtt_service.stop()
    print("\nMQTT service stopped")

if __name__ == "__main__":
    asyncio.run(test_complete_system())

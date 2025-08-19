#!/usr/bin/env python3
"""
Final test to show complete MQTT data format with device identification
"""
import sys
import os
import asyncio
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.services.mqtt_service import mqtt_service
from app.services.device_manager import device_manager
from app.mavlink.advanced_parser import AdvancedMavlinkParser

async def test_final_mqtt_format():
    """Test final MQTT data format with device identification"""
    print("=== Final MQTT Data Format Test ===")
    
    # Start MQTT service
    try:
        await mqtt_service.start()
        print("MQTT service started")
    except Exception as e:
        print(f"MQTT service start error: {e}")
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Test with a single device to show the complete data format
    test_data_hex = "fd2c00000109011800006088a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005501"
    test_data = bytes.fromhex(test_data_hex)
    client_address = "192.168.1.100:12345"
    
    print(f"Testing with GPS data from device...")
    print(f"Client: {client_address}")
    
    # Parse the packet
    result = parser.parse_packet(test_data, client_address)
    
    if result and result['message_type'] == 'GPS_RAW_INT':
        parsed_data = result.get('parsed_data', {})
        if 'lat' in parsed_data and 'lon' in parsed_data:
            lat = parsed_data['lat']
            lon = parsed_data['lon']
            alt = parsed_data.get('alt', 0.0)
            
            print(f"\nGPS Position: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
            
            # Show the complete MQTT data format
            device = device_manager.get_or_create_device(
                result['system_id'], 
                result['component_id'], 
                result['client_address']
            )
            
            gps_data = {
                "device_id": device.device_id,
                "system_id": result['system_id'],
                "component_id": result['component_id'],
                "client_address": result['client_address'],
                "device_type": device.device_type,
                "latitude": lat,
                "longitude": lon,
                "altitude": alt,
                "timestamp": "2025-08-19T16:30:00.000Z",
                "fix_type": parsed_data.get('fix_type', 0),
                "satellites_visible": parsed_data.get('satellites_visible', 0),
                "ground_speed": parsed_data.get('vel', 0.0),
                "course_over_ground": parsed_data.get('cog', 0.0),
                "message_sequence": result.get('sequence', 0),
                "message_type": result.get('message_type', 'GPS_RAW_INT'),
                "device_stats": {
                    "message_count": device.message_count,
                    "gps_fix_count": device.gps_fix_count,
                    "first_seen": device.first_seen.isoformat(),
                    "last_seen": device.last_seen.isoformat()
                },
                "raw_data": parsed_data
            }
            
            print(f"\n=== Complete MQTT GPS Data Format ===")
            print(json.dumps(gps_data, indent=2, ensure_ascii=False))
            
            # Show device manager status
            print(f"\n=== Device Manager Status ===")
            stats = device_manager.get_device_stats()
            print(f"Total devices: {stats['total_devices']}")
            print(f"Active devices: {stats['active_devices']}")
            print(f"Total messages: {stats['total_messages']}")
            print(f"Total GPS fixes: {stats['total_gps_fixes']}")
            
            # Show device details
            print(f"\n=== Device Details ===")
            print(f"Device ID: {device.device_id}")
            print(f"System ID: {device.system_id}")
            print(f"Component ID: {device.component_id}")
            print(f"Client Address: {device.client_address}")
            print(f"Messages: {device.message_count}")
            print(f"GPS Fixes: {device.gps_fix_count}")
            print(f"First Seen: {device.first_seen}")
            print(f"Last Seen: {device.last_seen}")
            
        else:
            print("No valid GPS position data found")
    else:
        print(f"Not a GPS message: {result['message_type'] if result else 'Parse failed'}")
    
    # Stop MQTT service
    await mqtt_service.stop()
    print("\nMQTT service stopped")

if __name__ == "__main__":
    asyncio.run(test_final_mqtt_format())

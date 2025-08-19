#!/usr/bin/env python3
"""
Test script for multi-device GPS tracking
"""
import sys
import os
import asyncio
import json
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.services.mqtt_service import mqtt_service
from app.services.device_manager import device_manager
from app.mavlink.advanced_parser import AdvancedMavlinkParser

async def test_multi_device():
    """Test multi-device GPS tracking"""
    print("=== Multi-Device GPS Tracking Test ===")
    
    # Start MQTT service
    try:
        await mqtt_service.start()
        print("MQTT service started")
    except Exception as e:
        print(f"MQTT service start error: {e}")
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Simulate multiple devices with different system IDs and client addresses
    test_scenarios = [
        {
            "name": "Device 1 (System 9, Client 192.168.1.100)",
            "data": "fd2c00000109011800006088a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005501",
            "client": "192.168.1.100:12345"
        },
        {
            "name": "Device 2 (System 10, Client 192.168.1.101)",
            "data": "fd2c0000020a011800006188a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005502",
            "client": "192.168.1.101:12346"
        },
        {
            "name": "Device 3 (System 9, Client 192.168.1.102)",
            "data": "fd2c00000309011800006288a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005503",
            "client": "192.168.1.102:12347"
        },
        {
            "name": "Device 4 (System 11, Client 192.168.1.103)",
            "data": "fd2c0000040b011800006388a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005504",
            "client": "192.168.1.103:12348"
        }
    ]
    
    print(f"\nTesting {len(test_scenarios)} different devices...")
    
    for i, scenario in enumerate(test_scenarios):
        print(f"\n--- {scenario['name']} ---")
        test_data = bytes.fromhex(scenario['data'])
        
        # Parse the packet
        result = parser.parse_packet(test_data, scenario['client'])
        
        if result and result['message_type'] == 'GPS_RAW_INT':
            parsed_data = result.get('parsed_data', {})
            if 'lat' in parsed_data and 'lon' in parsed_data:
                lat = parsed_data['lat']
                lon = parsed_data['lon']
                alt = parsed_data.get('alt', 0.0)
                
                print(f"GPS Position: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
                print(f"System ID: {result['system_id']}, Component ID: {result['component_id']}")
                print(f"Client: {scenario['client']}")
                
                # Wait a bit between devices
                await asyncio.sleep(0.5)
            else:
                print("? No valid GPS position data found")
        else:
            print(f"? Not a GPS message: {result['message_type'] if result else 'Parse failed'}")
    
    # Show device manager status
    print(f"\n=== Device Manager Status ===")
    stats = device_manager.get_device_stats()
    print(f"Total devices: {stats['total_devices']}")
    print(f"Active devices: {stats['active_devices']}")
    print(f"Total messages: {stats['total_messages']}")
    print(f"Total GPS fixes: {stats['total_gps_fixes']}")
    
    # Show all devices
    print(f"\n=== All Devices ===")
    all_devices = device_manager.get_all_devices()
    for device_id, device in all_devices.items():
        print(f"Device: {device_id}")
        print(f"  System ID: {device.system_id}, Component ID: {device.component_id}")
        print(f"  Client: {device.client_address}")
        print(f"  Messages: {device.message_count}, GPS Fixes: {device.gps_fix_count}")
        if device.last_position:
            print(f"  Last Position: ({device.last_position['latitude']:.6f}, {device.last_position['longitude']:.6f})")
        print(f"  Last Seen: {device.last_seen.strftime('%H:%M:%S')}")
        print()
    
    # Export device data
    print(f"\n=== Exported Device Data ===")
    export_data = device_manager.export_device_data()
    print(json.dumps(export_data, indent=2, ensure_ascii=False))
    
    # Stop MQTT service
    await mqtt_service.stop()
    print("\nMQTT service stopped")

if __name__ == "__main__":
    asyncio.run(test_multi_device())

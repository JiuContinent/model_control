#!/usr/bin/env python3
"""
Debug script for device manager
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.services.device_manager import device_manager
from app.mavlink.advanced_parser import AdvancedMavlinkParser

def test_device_manager_debug():
    """Debug device manager functionality"""
    print("=== Device Manager Debug Test ===")
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Test single device
    test_data_hex = "fd2c00000109011800006088a75600000000017a1a139653f8460ca800004f0072000100b438030ed3b400006f0b0000890b00005501"
    test_data = bytes.fromhex(test_data_hex)
    client_address = "192.168.1.100:12345"
    
    print(f"Testing with data: {test_data_hex}")
    print(f"Client: {client_address}")
    
    # Parse the packet
    result = parser.parse_packet(test_data, client_address)
    
    if result:
        print(f"Parse result:")
        print(f"  Message ID: {result['message_id']}")
        print(f"  Message Type: {result['message_type']}")
        print(f"  System ID: {result['system_id']}")
        print(f"  Component ID: {result['component_id']}")
        print(f"  Client Address: {result['client_address']}")
        
        if result['message_type'] == 'GPS_RAW_INT':
            parsed_data = result.get('parsed_data', {})
            if 'lat' in parsed_data and 'lon' in parsed_data:
                lat = parsed_data['lat']
                lon = parsed_data['lon']
                alt = parsed_data.get('alt', 0.0)
                
                print(f"GPS Position: ({lat:.6f}, {lon:.6f}) Altitude: {alt:.1f}m")
                
                # Manually test device manager
                print(f"\n--- Manual Device Manager Test ---")
                device = device_manager.get_or_create_device(
                    result['system_id'], 
                    result['component_id'], 
                    result['client_address']
                )
                print(f"Device ID: {device.device_id}")
                print(f"Device created: {device.device_id in device_manager.devices}")
                
                # Update device
                gps_data = {
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": alt,
                    "fix_type": parsed_data.get('fix_type', 0),
                    "satellites_visible": parsed_data.get('satellites_visible', 0)
                }
                device_manager.update_device_gps(device.device_id, gps_data)
                
                print(f"Device updated: {device.message_count} messages, {device.gps_fix_count} GPS fixes")
                
                # Check device manager status
                print(f"\n--- Device Manager Status ---")
                stats = device_manager.get_device_stats()
                print(f"Total devices: {stats['total_devices']}")
                print(f"Active devices: {stats['active_devices']}")
                
                # Show all devices
                all_devices = device_manager.get_all_devices()
                print(f"All devices: {list(all_devices.keys())}")
                
            else:
                print("No valid GPS position data found")
        else:
            print(f"Not a GPS message: {result['message_type']}")
    else:
        print("Failed to parse packet")

if __name__ == "__main__":
    test_device_manager_debug()

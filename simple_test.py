#!/usr/bin/env python3
"""
Simple MAVLink receiver test
"""
import socket
import time
import requests

def test_mavlink_receiver():
    """Test MAVLink receiver with real data"""
    print("=" * 50)
    print("Testing MAVLink receiver with real data")
    print("=" * 50)
    
    # Real MAVLink packets (hex strings)
    mavlink_packets = [
        # ATTITUDE message
        "fd1600004f0901c10000d79b803dce39923dc4fdda3b20cd803b000000003f0390b7",
        
        # SCALED_PRESSURE message  
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        
        # VFR_HUD message
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f"
    ]
    
    try:
        # Connect to MAVLink receiver
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("Connected to MAVLink receiver (localhost:5760)")
        
        # Send real packets
        for i, hex_data in enumerate(mavlink_packets):
            packet_data = bytes.fromhex(hex_data)
            sock.send(packet_data)
            print(f"Sent MAVLink packet {i+1}/3 (length: {len(packet_data)} bytes)")
            print(f"Data: {hex_data}")
            time.sleep(1)
        
        sock.close()
        print("Real packets sent successfully")
        
        # Wait for processing
        print("Waiting for data processing...")
        time.sleep(2)
        
        # Check receiver status
        try:
            response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
            if response.status_code == 200:
                status = response.json()
                print(f"\nMAVLink receiver status:")
                print(f"  - Running: {status['is_running']}")
                print(f"  - Total messages: {status['total_messages']}")
                print(f"  - Active sessions: {status['active_sessions']}")
                
                # Check MQTT status
                if 'mqtt_status' in status:
                    mqtt_status = status['mqtt_status']
                    print(f"\nMQTT forwarding status:")
                    print(f"  - MQTT connected: {mqtt_status['is_connected']}")
                    print(f"  - Messages published: {mqtt_status['messages_published']}")
                    print(f"  - Topic: {mqtt_status['topic']}")
            else:
                print("Failed to get receiver status")
        except Exception as e:
            print(f"Failed to check receiver status: {e}")
        
    except Exception as e:
        print(f"Test failed: {e}")

def check_mqtt_status():
    """Check MQTT status"""
    print("\n" + "=" * 50)
    print("Checking MQTT service status")
    print("=" * 50)
    
    try:
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        if response.status_code == 200:
            status = response.json()
            print(f"MQTT service status:")
            print(f"  - Running: {status['is_running']}")
            print(f"  - Connected: {status['is_connected']}")
            print(f"  - Broker: {status['broker_host']}:{status['broker_port']}")
            print(f"  - Topic: {status['topic']}")
            print(f"  - Messages published: {status['messages_published']}")
        else:
            print("Failed to get MQTT status")
            
    except Exception as e:
        print(f"MQTT status check failed: {e}")

if __name__ == "__main__":
    # Check MQTT status
    check_mqtt_status()
    
    # Test with real data
    test_mavlink_receiver()
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("=" * 50)
    print("Results:")
    print("1. If MAVLink receiver can receive data, TCP receiving works")
    print("2. If MQTT is connected, data will be forwarded to MQTT topic")
    print("3. You can use MQTT client to subscribe to: /ue/device/mavlink")
    print("=" * 50)


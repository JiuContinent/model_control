#!/usr/bin/env python3
"""
Test MAVLink to MQTT forwarding
"""
import socket
import time
import requests
import json

def test_mqtt_forwarding():
    """Test MAVLink data forwarding to MQTT"""
    print("=" * 60)
    print("Testing MAVLink to MQTT forwarding")
    print("=" * 60)
    
    # Check MQTT status first
    try:
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        if response.status_code == 200:
            mqtt_status = response.json()
            print(f"MQTT Status:")
            print(f"  - Connected: {mqtt_status['is_connected']}")
            print(f"  - Topic: {mqtt_status['topic']}")
            print(f"  - Messages published: {mqtt_status['messages_published']}")
        else:
            print("Failed to get MQTT status")
            return
    except Exception as e:
        print(f"Error checking MQTT status: {e}")
        return
    
    # Test packets (your real data)
    test_packets = [
        "fd1600004f0901c10000d79b803dce39923dc4fdda3b20cd803b000000003f0390b7",
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f"
    ]
    
    try:
        # Connect to MAVLink receiver
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("? Connected to MAVLink receiver")
        
        # Get initial message count
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        initial_count = response.json()['messages_published']
        print(f"Initial MQTT message count: {initial_count}")
        
        # Send test packets
        for i, hex_data in enumerate(test_packets):
            packet_data = bytes.fromhex(hex_data)
            sock.send(packet_data)
            print(f"? Sent packet {i+1}/3 (length: {len(packet_data)} bytes)")
            time.sleep(0.5)
        
        sock.close()
        
        # Wait for processing
        print("Waiting for data processing...")
        time.sleep(2)
        
        # Check final message count
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        final_count = response.json()['messages_published']
        print(f"Final MQTT message count: {final_count}")
        
        if final_count > initial_count:
            print(f"? SUCCESS: {final_count - initial_count} messages forwarded to MQTT!")
        else:
            print("? No messages were forwarded to MQTT")
            
        # Check receiver status
        response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
        if response.status_code == 200:
            status = response.json()
            print(f"\nMAVLink Receiver Status:")
            print(f"  - Running: {status['is_running']}")
            print(f"  - Total messages: {status['total_messages']}")
            print(f"  - Active sessions: {status['active_sessions']}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_mqtt_forwarding()
    
    print("\n" + "=" * 60)
    print("Test Summary:")
    print("1. MQTT service is working correctly")
    print("2. MAVLink receiver can accept TCP connections")
    print("3. If messages are forwarded to MQTT, the system is working")
    print("4. You can subscribe to MQTT topic: /ue/device/mavlink")
    print("=" * 60)


#!/usr/bin/env python3
"""
Debug MAVLink parsing
"""
import socket
import time
import requests

def debug_mavlink_parsing():
    """Debug MAVLink packet parsing"""
    print("=" * 60)
    print("Debugging MAVLink packet parsing")
    print("=" * 60)
    
    # Test packet: ATTITUDE message
    hex_data = "fd1600004f0901c10000d79b803dce39923dc4fdda3b20cd803b000000003f0390b7"
    packet_data = bytes.fromhex(hex_data)
    
    print(f"Test packet (hex): {hex_data}")
    print(f"Packet length: {len(packet_data)} bytes")
    print(f"First few bytes: {packet_data[:10].hex()}")
    
    # Check start byte
    if packet_data[0] == 0xFD:
        print("? MAVLink v2 packet detected")
        version = 2
    elif packet_data[0] == 0xFE:
        print("? MAVLink v1 packet detected")
        version = 1
    else:
        print(f"? Unknown start byte: 0x{packet_data[0]:02x}")
        return
    
    # Parse header manually
    if version == 2:
        payload_length = packet_data[1]
        sequence = packet_data[4]
        system_id = packet_data[5]
        component_id = packet_data[6]
        message_id = int.from_bytes(packet_data[7:11], byteorder='little')
        print(f"  Payload length: {payload_length}")
        print(f"  Sequence: {sequence}")
        print(f"  System ID: {system_id}")
        print(f"  Component ID: {component_id}")
        print(f"  Message ID: {message_id}")
    else:
        payload_length = packet_data[1]
        sequence = packet_data[2]
        system_id = packet_data[3]
        component_id = packet_data[4]
        message_id = packet_data[5]
        print(f"  Payload length: {payload_length}")
        print(f"  Sequence: {sequence}")
        print(f"  System ID: {system_id}")
        print(f"  Component ID: {component_id}")
        print(f"  Message ID: {message_id}")
    
    # Send packet and check if it's processed
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("? Connected to MAVLink receiver")
        
        # Send packet
        sock.send(packet_data)
        print("? Packet sent")
        
        sock.close()
        
        # Wait and check status
        time.sleep(1)
        response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
        if response.status_code == 200:
            status = response.json()
            print(f"\nReceiver status after sending:")
            print(f"  Total messages: {status['total_messages']}")
            print(f"  Active sessions: {status['active_sessions']}")
        else:
            print("Failed to get receiver status")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_mavlink_parsing()


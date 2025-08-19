#!/usr/bin/env python3
"""
Test with real UDP data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.advanced_parser import AdvancedMavlinkParser
from datetime import datetime

def test_real_data():
    """Test with real UDP data"""
    print("=" * 70)
    print("Test with real UDP data")
    print("=" * 70)
    
    parser = AdvancedMavlinkParser()
    
    # Your actual UDP data
    real_data = bytes.fromhex("fd8000e00120002ac3a1dcd38964c07e682978a1f39f46a0")
    
    print(f"Testing data: {real_data.hex()}")
    print(f"Length: {len(real_data)} bytes")
    print()
    
    # Parse the data
    message = parser.parse_packet(real_data, "test_client")
    
    if message:
        print("? Data parsed successfully!")
        print(f"  Message type: {message['message_type']}")
        print(f"  System ID: {message['system_id']}")
        print(f"  Component ID: {message['component_id']}")
        print(f"  Sequence: {message['sequence']}")
        print(f"  Expected payload length: {message['payload_length']}")
        print(f"  Actual payload length: {message['actual_payload_length']}")
        print(f"  Is truncated: {message['is_truncated']}")
        
        if 'parsed_data' in message and message['parsed_data']:
            print(f"  Parsed data: {message['parsed_data']}")
        
        print()
        print("Expected output format:")
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')[:-3]}] Received {len(real_data)} bytes UDP data (sample rate: 1/10):")
        print(f"  Raw data (hex): {real_data.hex()}")
        print(f"  Parsed MAVLink message: System ID={message['system_id']}, Type={message['message_type']}")
        if message.get('is_truncated', False):
            print(f"  Note: Packet truncated (expected {message['payload_length']} bytes, got {message['actual_payload_length']})")
        print(f"    Equipment-{message['system_id']}: Position(0.000000, 0.000000) Altitude 0.0m Battery 100%")
    else:
        print("? Data parsing failed")
    
    print("=" * 70)

if __name__ == "__main__":
    test_real_data()


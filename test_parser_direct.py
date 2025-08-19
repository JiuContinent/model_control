#!/usr/bin/env python3
"""
Direct test MAVLink parser
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.advanced_parser import AdvancedMavlinkParser

def test_parser():
    """Test parser"""
    print("=" * 70)
    print("Direct test MAVLink parser")
    print("=" * 70)
    
    # Create parser
    parser = AdvancedMavlinkParser()
    
    # Real MAVLink packets (hex strings)
    mavlink_packets = [
        # ATTITUDE message
        "fd1c0000a009011e00006d453d00008b5939a25e743d284441c0ead115bebd954cbd864789bcf113",
        
        # SCALED_PRESSURE message
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        
        # VFR_HUD message
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f",
        
        # SYSTEM_TIME message
        "fd0b0000c809010200007ac33ca2a03c060075473dab22",
        
        # MEMINFO message
        "fd070000d209019800000000ffffd81a03c244",
        
        # RAW_IMU message
        "fd1d0000e609011b0000bcc366ef00000000410030001cfc0400e5ff1100ecfe1500700100e313d4a0",
        
        # VIBRATION message
        "fd140000f00901f10000511367ef00000000916b333d95717c3dc0ad693dcf76",
        
        # MISSION_CURRENT message
        "fd010000fa09012a0000003473",
        
        # SCALED_IMU2 message
        "fd1800000409017400005d4b3d0046001d0019fcfbff09000400f1fed2ff7401ff13a39d",
        
        # BATTERY_STATUS message
        "fd2900000e0901930000ffffffffffffffffff7f345affffffffffffffffffffffffffffffffffffffff000000ff000000000189ec",
        
        # SYS_STATUS message
        "fd1f00001809010100003ffc61132f8061022f8070037c00315affff000000000000000000000000ffb35f",
        
        # SERVO_OUTPUT_RAW message
        "fd210000220901240000e80576efc805dc054c044c04000000000000000000000000000000e803e803e8036f37",
        
        # EKF_STATUS_REPORT message
        "fd1600002c0901c10000dd61cc3da34f023dfc0f9c3d085d363d000000003f03f722",
        
        # POWER_STATUS message
        "fd0500003609017d00000c15000001a37e"
    ]
    
    print("Start parsing MAVLink packets...")
    print()
    
    # Parse each packet
    for i, hex_data in enumerate(mavlink_packets):
        # Convert hex string to bytes
        packet_data = bytes.fromhex(hex_data)
        
        # Parse packet
        message = parser.parse_packet(packet_data, "test_client")
        
        if message:
            print(f"? Packet {i+1} parsed successfully:")
            print(f"  Message type: {message['message_type']}")
            print(f"  System ID: {message['system_id']}")
            print(f"  Component ID: {message['component_id']}")
            print(f"  Sequence: {message['sequence']}")
            print(f"  Data length: {message['payload_length']}")
            
            # Show parsed data
            if 'parsed_data' in message and message['parsed_data']:
                print(f"  Parsed data: {message['parsed_data']}")
            
            print()
        else:
            print(f"? Packet {i+1} parsing failed")
            print(f"  Data length: {len(packet_data)}")
            print(f"  First bytes: {packet_data[:10].hex()}")
            print()
    
    print("=" * 70)
    print("Test completed!")
    print("=" * 70)
    print(f"Total packets parsed: {parser.packet_count}")
    print("If all packets parsed successfully, the parser is working correctly")

if __name__ == "__main__":
    test_parser()

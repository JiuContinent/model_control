#!/usr/bin/env python3
"""
Test UDP receiver fix
"""
import asyncio
import socket
import time
from datetime import datetime

async def test_udp_receiver():
    """Test UDP receiver"""
    print("=" * 70)
    print("Test UDP MAVLink receiver fix")
    print("=" * 70)
    
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
    
    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        print("? Start sending MAVLink packets to UDP receiver...")
        
        # Send real packets
        for i, hex_data in enumerate(mavlink_packets):
            # Convert hex string to bytes
            packet_data = bytes.fromhex(hex_data)
            
            # Send packet to UDP receiver
            sock.sendto(packet_data, ('localhost', 14550))
            print(f"? Sent MAVLink packet {i+1}/{len(mavlink_packets)} (length: {len(packet_data)} bytes)")
            print(f"  Data: {hex_data}")
            
            # Wait a bit
            time.sleep(0.1)
        
        sock.close()
        print("? Packet sending completed")
        
        # Wait for processing
        print("Waiting for data processing...")
        time.sleep(2)
        
        print("\n" + "=" * 70)
        print("Test completed!")
        print("=" * 70)
        print("If the fix is successful, you should see output like:")
        print("[17:47:54.857] Received 28 bytes UDP data (sample rate: 1/10):")
        print("  Raw data (hex): fd1c0000a009011e00006d453d00008b5939a25e743d284441c0ead115bebd954cbd864789bcf113")
        print("  Parsed MAVLink message: System ID=9, Type=ATTITUDE")
        print("    Equipment-9: Position(0.000000, 0.000000) Altitude 0.0m Battery 100%")
        print("=" * 70)
        
    except Exception as e:
        print(f"? Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_udp_receiver())


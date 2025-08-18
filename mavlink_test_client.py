#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MAVLink Test Client for sending specific test data
Sends the exact MAVLink packets provided by the user
"""
import socket
import time
import struct
from datetime import datetime


class MavlinkTestClient:
    """UDP client for sending specific MAVLink test data"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 14550):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sequence = 0
        
    def send_hex_packet(self, hex_string: str, description: str = ""):
        """Send a packet from hex string"""
        try:
            # Remove spaces and convert hex to bytes
            hex_bytes = bytes.fromhex(hex_string.replace(" ", ""))
            self.socket.sendto(hex_bytes, (self.host, self.port))
            
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{timestamp}] Sent {len(hex_bytes)} bytes of UDP data:")
            print(f"  Raw data (hex): {hex_string}")
            if description:
                print(f"  Description: {description}")
            print()
            
        except Exception as e:
            print(f"Error sending packet: {e}")
    
    def send_test_sequence(self, interval: float = 0.3):
        """Send the test sequence of MAVLink packets"""
        print(f"Starting to send MAVLink test data to {self.host}:{self.port}")
        print("=" * 60)
        
        # Test packet 1: AHRS message
        packet1 = "fd1c0000800901a30000f1b9cbb9ae1e923bcbef09bb0000000000000000257ac03d6413e03b228e"
        self.send_hex_packet(packet1, "AHRS message - System ID=9")
        time.sleep(interval)
        
        # Test packet 2: MISSION_CURRENT message
        packet2 = "fd0100008a09012a0000004dfb"
        self.send_hex_packet(packet2, "MISSION_CURRENT message - System ID=9")
        time.sleep(interval)
        
        # Test packet 3: GPS_RAW_INT message
        packet3 = "fd2c0000940901180000c0fdceef000000008d781a13e259f846cef900005a006000260026730411960601002d0e0000211200000703cb54"
        self.send_hex_packet(packet3, "GPS_RAW_INT message - System ID=9, Position(32.050190, 119.068106)")
        time.sleep(interval)
        
        # Test packet 4: SCALED_IMU3 message
        packet4 = "fd1800009e0901810000c1643d0075002f0008fcfeffffff03000000000000009411e002"
        self.send_hex_packet(packet4, "SCALED_IMU3 message - System ID=9")
        time.sleep(interval)
        
        print("=" * 60)
        print("Test data sending completed")
    
    def send_continuous_sequence(self, count: int = 10, interval: float = 0.3):
        """Send the test sequence multiple times"""
        print(f"Starting continuous test sequence {count} times, interval {interval} seconds")
        print("=" * 60)
        
        for i in range(count):
            print(f"\n--- Round {i+1}/{count} ---")
            self.send_test_sequence(interval)
            if i < count - 1:  # Don't sleep after last round
                time.sleep(interval * 2)  # Extra pause between rounds
        
        print("=" * 60)
        print("Continuous test completed")
    
    def send_single_packet(self, packet_type: str = "ahrs"):
        """Send a single packet of specified type"""
        packets = {
            "ahrs": ("fd1c0000800901a30000f1b9cbb9ae1e923bcbef09bb0000000000000000257ac03d6413e03b228e", "AHRS message"),
            "mission": ("fd0100008a09012a0000004dfb", "MISSION_CURRENT message"),
            "gps": ("fd2c0000940901180000c0fdceef000000008d781a13e259f846cef900005a006000260026730411960601002d0e0000211200000703cb54", "GPS_RAW_INT message"),
            "imu": ("fd1800009e0901810000c1643d0075002f0008fcfeffffff03000000000000009411e002", "SCALED_IMU3 message")
        }
        
        if packet_type in packets:
            hex_data, description = packets[packet_type]
            self.send_hex_packet(hex_data, description)
        else:
            print(f"Unknown packet type: {packet_type}")
            print("Available types: ahrs, mission, gps, imu")
    
    def close(self):
        """Close the socket"""
        self.socket.close()


def main():
    """Main function"""
    print("MAVLink Test Client")
    print("=" * 30)
    
    # Create client
    client = MavlinkTestClient("127.0.0.1", 14550)
    
    try:
        while True:
            print("\nSelect operation:")
            print("1. Send single test sequence")
            print("2. Send continuous test sequence")
            print("3. Send single packet")
            print("4. Send custom hex data")
            print("5. Exit")
            
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == "1":
                interval = float(input("Packet interval in seconds (default 0.3): ") or "0.3")
                client.send_test_sequence(interval)
                
            elif choice == "2":
                count = int(input("Repeat count (default 10): ") or "10")
                interval = float(input("Packet interval in seconds (default 0.3): ") or "0.3")
                client.send_continuous_sequence(count, interval)
                
            elif choice == "3":
                print("Available packet types:")
                print("- ahrs: AHRS message")
                print("- mission: MISSION_CURRENT message")
                print("- gps: GPS_RAW_INT message")
                print("- imu: SCALED_IMU3 message")
                packet_type = input("Enter packet type: ").strip()
                client.send_single_packet(packet_type)
                
            elif choice == "4":
                hex_data = input("Enter hex data (e.g., fd1c0000800901a30000...): ")
                if hex_data:
                    client.send_hex_packet(hex_data, "Custom packet")
                    
            elif choice == "5":
                break
            else:
                print("Invalid choice, please try again")
                
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        client.close()
        print("Client closed")


if __name__ == "__main__":
    main()

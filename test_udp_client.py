#!/usr/bin/env python3
"""
UDP Test Client for MAVLink
Sends MAVLink packets to test UDP receiver
"""
import socket
import time
import struct
import random
from datetime import datetime


class MavlinkUdpClient:
    """UDP client for testing MAVLink receiver"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 14550):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sequence = 0
        
    def create_mavlink_packet(self, message_id: int, system_id: int = 1, 
                             component_id: int = 1, payload: bytes = b"") -> bytes:
        """Create a MAVLink v2 packet"""
        # MAVLink v2 packet structure:
        # FD + length + sequence + system_id + component_id + message_id + payload + CRC
        
        # Packet header
        packet = bytearray()
        packet.append(0xFD)  # MAVLink v2 signature
        packet.append(len(payload))  # Payload length
        packet.append(self.sequence)  # Sequence number
        packet.append(system_id)  # System ID
        packet.append(component_id)  # Component ID
        
        # Message ID (16-bit, little-endian)
        packet.extend(struct.pack('<H', message_id))
        
        # Payload
        packet.extend(payload)
        
        # Simple CRC (not real MAVLink CRC, just for testing)
        crc = sum(packet) & 0xFF
        packet.append(crc)
        
        self.sequence = (self.sequence + 1) % 256
        return bytes(packet)
    
    def send_packet(self, packet: bytes):
        """Send packet to UDP receiver"""
        try:
            self.socket.sendto(packet, (self.host, self.port))
            print(f"Sent {len(packet)} bytes: {' '.join(f'{b:02X}' for b in packet)}")
        except Exception as e:
            print(f"Error sending packet: {e}")
    
    def send_test_packets(self, count: int = 10, interval: float = 1.0):
        """Send multiple test packets"""
        print(f"Sending {count} test packets to {self.host}:{self.port}")
        print("=" * 50)
        
        for i in range(count):
            # Create different message types
            message_id = random.randint(0, 255)
            system_id = random.randint(1, 10)
            component_id = random.randint(1, 5)
            
            # Create sample payload
            payload = struct.pack('<f', random.uniform(0, 100))  # Random float
            
            # Create and send packet
            packet = self.create_mavlink_packet(message_id, system_id, component_id, payload)
            self.send_packet(packet)
            
            if i < count - 1:  # Don't sleep after last packet
                time.sleep(interval)
        
        print("=" * 50)
        print(f"Sent {count} packets")
    
    def send_specific_packet(self, hex_string: str):
        """Send a specific packet from hex string"""
        try:
            # Remove spaces and convert hex to bytes
            hex_bytes = bytes.fromhex(hex_string.replace(" ", ""))
            self.send_packet(hex_bytes)
        except Exception as e:
            print(f"Error sending hex packet: {e}")
    
    def close(self):
        """Close the socket"""
        self.socket.close()


def main():
    """Main function"""
    print("MAVLink UDP Test Client")
    print("=" * 30)
    
    # Create client
    client = MavlinkUdpClient("127.0.0.1", 14550)
    
    try:
        while True:
            print("\nSelect operation:")
            print("1. Send test packets")
            print("2. Send specific packet")
            print("3. Continuous sending")
            print("4. Exit")
            
            choice = input("Enter choice (1-4): ").strip()
            
            if choice == "1":
                count = int(input("Number of packets (default 10): ") or "10")
                interval = float(input("Interval in seconds (default 1.0): ") or "1.0")
                client.send_test_packets(count, interval)
                
            elif choice == "2":
                hex_data = input("Enter hex data (e.g., FD 11 00 00 86 01 01): ")
                if hex_data:
                    client.send_specific_packet(hex_data)
                    
            elif choice == "3":
                print("Starting continuous packet sending... (Press Ctrl+C to stop)")
                try:
                    while True:
                        message_id = random.randint(0, 255)
                        system_id = random.randint(1, 10)
                        component_id = random.randint(1, 5)
                        payload = struct.pack('<f', random.uniform(0, 100))
                        
                        packet = client.create_mavlink_packet(message_id, system_id, component_id, payload)
                        client.send_packet(packet)
                        time.sleep(0.5)  # 500ms interval
                        
                except KeyboardInterrupt:
                    print("\nStopped continuous sending")
                    
            elif choice == "4":
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

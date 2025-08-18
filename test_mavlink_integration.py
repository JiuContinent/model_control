#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import time
import sys
import os
import threading
from datetime import datetime

# Add src to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.udp_receiver import get_udp_receiver, start_udp_receiver, stop_udp_receiver


class MavlinkIntegrationTest:
    """MAVLink integration test"""
    
    def __init__(self):
        self.receiver = get_udp_receiver()
        self.test_data = [
            ("fd1c0000800901a30000f1b9cbb9ae1e923bcbef09bb0000000000000000257ac03d6413e03b228e", "AHRS message"),
            ("fd0100008a09012a0000004dfb", "MISSION_CURRENT message"),
            ("fd2c0000940901180000c0fdceef000000008d781a13e259f846cef900005a006000260026730411960601002d0e0000211200000703cb54", "GPS_RAW_INT message"),
            ("fd1800009e0901810000c1643d0075002f0008fcfeffffff03000000000000009411e002", "SCALED_IMU3 message")
        ]
    
    async def start_receiver(self):
        """Start the UDP receiver"""
        print("Starting MAVLink UDP receiver...")
        await start_udp_receiver()
        print("Receiver started, listening on port 14550")
    
    async def stop_receiver(self):
        """Stop the UDP receiver"""
        print("Stopping MAVLink UDP receiver...")
        await stop_udp_receiver()
        print("Receiver stopped")
    
    def send_test_data(self, host: str = "127.0.0.1", port: int = 14550, interval: float = 0.5):
        """Send test data in a separate thread"""
        import socket
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            print(f"Starting to send test data to {host}:{port}")
            print("=" * 60)
            
            for i, (hex_data, description) in enumerate(self.test_data, 1):
                # Convert hex to bytes
                data = bytes.fromhex(hex_data.replace(" ", ""))
                
                # Send data
                sock.sendto(data, (host, port))
                
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                print(f"[{timestamp}] Sending packet {i}: {description}")
                print(f"  Data length: {len(data)} bytes")
                print(f"  Hex data: {hex_data}")
                print()
                
                time.sleep(interval)
            
            print("=" * 60)
            print("Test data sending completed")
            
        except Exception as e:
            print(f"Error sending data: {e}")
        finally:
            sock.close()
    
    def run_sender_thread(self, host: str = "127.0.0.1", port: int = 14550, interval: float = 0.5):
        """Run sender in a separate thread"""
        thread = threading.Thread(
            target=self.send_test_data,
            args=(host, port, interval),
            daemon=True
        )
        thread.start()
        return thread
    
    def show_results(self):
        """Show test results"""
        print("\n" + "=" * 60)
        print("Test Results")
        print("=" * 60)
        
        # Show receiver stats
        stats = self.receiver.get_stats()
        print(f"Receiver status: {'Running' if stats['is_running'] else 'Stopped'}")
        print(f"Received messages: {stats['stored_messages']}")
        print(f"Active sessions: {stats['active_sessions']}")
        
        # Show recent messages
        messages = self.receiver.get_messages(10)
        print(f"\nRecently received messages ({len(messages)}):")
        
        for i, msg in enumerate(reversed(messages), 1):
            print(f"\nMessage {i}:")
            print(f"  Message ID: {msg['message_id']}")
            print(f"  System ID: {msg['system_id']}")
            print(f"  Component ID: {msg['component_id']}")
            print(f"  Client address: {msg['client_address']}")
            print(f"  Packet length: {msg['packet_length']} bytes")
            print(f"  Timestamp: {msg['timestamp']}")
        
        # Show sessions
        sessions = self.receiver.get_sessions()
        print(f"\nActive sessions ({len(sessions)}):")
        
        for i, session in enumerate(sessions, 1):
            print(f"\nSession {i}:")
            print(f"  System ID: {session['system_id']}")
            print(f"  Client address: {session['client_address']}")
            print(f"  Message count: {session['message_count']}")
            print(f"  First seen: {session['first_seen']}")
            print(f"  Last seen: {session['last_seen']}")
    
    async def run_test(self, wait_time: float = 3.0):
        """Run the complete integration test"""
        print("MAVLink Integration Test")
        print("=" * 30)
        
        try:
            # Start receiver
            await self.start_receiver()
            
            # Wait a moment for receiver to fully start
            await asyncio.sleep(1)
            
            # Start sender in background thread
            sender_thread = self.run_sender_thread(interval=0.5)
            
            # Wait for sender to complete
            print(f"Waiting {wait_time} seconds for data sending to complete...")
            await asyncio.sleep(wait_time)
            
            # Show results
            self.show_results()
            
            # Ask if user wants to continue monitoring
            print("\n" + "-" * 40)
            choice = input("Continue monitoring receiver? (y/n): ").strip().lower()
            
            if choice == 'y':
                print("Starting real-time monitoring (Press Ctrl+C to stop)...")
                try:
                    while True:
                        current_messages = len(self.receiver.get_messages())
                        current_sessions = len(self.receiver.get_sessions())
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        print(f"[{timestamp}] Messages: {current_messages}, Sessions: {current_sessions}")
                        await asyncio.sleep(2)
                except KeyboardInterrupt:
                    print("\nMonitoring stopped")
            
        except Exception as e:
            print(f"Error during test: {e}")
        finally:
            await self.stop_receiver()
            print("Integration test completed")


async def main():
    """Main function"""
    test = MavlinkIntegrationTest()
    await test.run_test()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import asyncio
import time
import sys
import os

# Add src to path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app.mavlink.udp_receiver import get_udp_receiver, start_udp_receiver, stop_udp_receiver


class MavlinkVerifier:
    """MAVLink verification utility"""
    
    def __init__(self):
        self.receiver = get_udp_receiver()
        self.is_running = False
    
    async def start_receiver(self):
        """Start the UDP receiver"""
        if not self.is_running:
            await start_udp_receiver()
            self.is_running = True
            print("MAVLink UDP receiver started")
    
    async def stop_receiver(self):
        """Stop the UDP receiver"""
        if self.is_running:
            await stop_udp_receiver()
            self.is_running = False
            print("MAVLink UDP receiver stopped")
    
    def show_status(self):
        """Show receiver status"""
        stats = self.receiver.get_stats()
        print("\n=== MAVLink Receiver Status ===")
        print(f"Running status: {'Running' if stats['is_running'] else 'Stopped'}")
        print(f"Listen address: {stats['host']}:{stats['port']}")
        print(f"Stored messages: {stats['stored_messages']}")
        print(f"Active sessions: {stats['active_sessions']}")
        print(f"Parser stats: {stats['parser_stats']}")
        print(f"Timestamp: {stats['timestamp']}")
    
    def show_messages(self, limit: int = 10):
        """Show recent messages"""
        messages = self.receiver.get_messages(limit)
        print(f"\n=== Recent {len(messages)} Messages ===")
        
        if not messages:
            print("No messages received")
            return
        
        for i, msg in enumerate(reversed(messages), 1):
            print(f"\nMessage {i}:")
            print(f"  Message ID: {msg['message_id']}")
            print(f"  System ID: {msg['system_id']}")
            print(f"  Component ID: {msg['component_id']}")
            print(f"  Sequence: {msg['sequence']}")
            print(f"  Client address: {msg['client_address']}")
            print(f"  Packet length: {msg['packet_length']} bytes")
            print(f"  Timestamp: {msg['timestamp']}")
            print(f"  Valid: {msg['is_valid']}")
    
    def show_sessions(self):
        """Show active sessions"""
        sessions = self.receiver.get_sessions()
        print(f"\n=== Active Sessions ({len(sessions)}) ===")
        
        if not sessions:
            print("No active sessions")
            return
        
        for i, session in enumerate(sessions, 1):
            print(f"\nSession {i}:")
            print(f"  System ID: {session['system_id']}")
            print(f"  Client address: {session['client_address']}")
            print(f"  First seen: {session['first_seen']}")
            print(f"  Last seen: {session['last_seen']}")
            print(f"  Message count: {session['message_count']}")
            print(f"  Active status: {session['is_active']}")
    
    async def monitor_realtime(self, duration: int = 30):
        """Monitor messages in real-time"""
        print(f"\nStarting real-time monitoring for {duration} seconds...")
        print("Press Ctrl+C to stop monitoring")
        print("-" * 50)
        
        start_time = time.time()
        initial_count = len(self.receiver.get_messages())
        
        try:
            while time.time() - start_time < duration:
                current_count = len(self.receiver.get_messages())
                new_messages = current_count - initial_count
                
                if new_messages > 0:
                    print(f"[{time.strftime('%H:%M:%S')}] Received {new_messages} new messages")
                    initial_count = current_count
                
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
        
        final_count = len(self.receiver.get_messages())
        total_new = final_count - initial_count
        print(f"\nTotal {total_new} new messages received during monitoring")


async def main():
    """Main function"""
    print("MAVLink Verification Tool")
    print("=" * 30)
    
    verifier = MavlinkVerifier()
    
    try:
        # Start receiver
        await verifier.start_receiver()
        
        while True:
            print("\nSelect operation:")
            print("1. Show receiver status")
            print("2. Show recent messages")
            print("3. Show active sessions")
            print("4. Real-time monitoring")
            print("5. Exit")
            
            choice = input("Enter choice (1-5): ").strip()
            
            if choice == "1":
                verifier.show_status()
                
            elif choice == "2":
                limit = int(input("Number of messages to show (default 10): ") or "10")
                verifier.show_messages(limit)
                
            elif choice == "3":
                verifier.show_sessions()
                
            elif choice == "4":
                duration = int(input("Monitoring duration in seconds (default 30): ") or "30")
                await verifier.monitor_realtime(duration)
                
            elif choice == "5":
                break
            else:
                print("Invalid choice, please try again")
                
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    finally:
        await verifier.stop_receiver()
        print("Verification tool closed")


if __name__ == "__main__":
    asyncio.run(main())

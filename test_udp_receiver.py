#!/usr/bin/env python3
"""
UDP Receiver Test Script
测试UDP接收器是否正常工作
"""
import requests
import time
import json
from datetime import datetime


def test_udp_receiver():
    """Test UDP receiver functionality"""
    base_url = "http://localhost:8000/api/v1/mavlink"
    
    print("=" * 50)
    print("UDP Receiver Test")
    print("=" * 50)
    
    # 1. Check UDP receiver status
    print("\n1. Checking UDP receiver status...")
    try:
        response = requests.get(f"{base_url}/udp/status")
        if response.status_code == 200:
            status = response.json()
            print(f"? UDP receiver status: {json.dumps(status, indent=2, ensure_ascii=False)}")
        else:
            print(f"? Failed to get UDP status: {response.status_code}")
            return False
    except Exception as e:
        print(f"? Connection failed: {e}")
        return False
    
    # 2. Check UDP messages
    print("\n2. Checking UDP messages...")
    try:
        response = requests.get(f"{base_url}/udp/messages?limit=10")
        if response.status_code == 200:
            messages = response.json()
            print(f"? Current UDP message count: {messages['total']}")
            if messages['messages']:
                print("Latest messages:")
                for msg in messages['messages'][-3:]:  # Show last 3 messages
                    print(f"  - {msg}")
        else:
            print(f"? Failed to get UDP messages: {response.status_code}")
    except Exception as e:
        print(f"? Failed to get UDP messages: {e}")
    
    # 3. Check UDP sessions
    print("\n3. Checking UDP sessions...")
    try:
        response = requests.get(f"{base_url}/udp/sessions")
        if response.status_code == 200:
            sessions = response.json()
            print(f"? Current UDP session count: {sessions['total']}")
            if sessions['sessions']:
                print("Active sessions:")
                for session in sessions['sessions']:
                    print(f"  - {session}")
        else:
            print(f"? Failed to get UDP sessions: {response.status_code}")
    except Exception as e:
        print(f"? Failed to get UDP sessions: {e}")
    
    # 4. Check TCP receiver status (for comparison)
    print("\n4. Checking TCP receiver status (for comparison)...")
    try:
        response = requests.get(f"{base_url}/receiver/status")
        if response.status_code == 200:
            tcp_status = response.json()
            print(f"? TCP receiver status: {json.dumps(tcp_status, indent=2, ensure_ascii=False)}")
        else:
            print(f"? Failed to get TCP status: {response.status_code}")
    except Exception as e:
        print(f"? Failed to get TCP status: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed")
    print("=" * 50)
    
    return True


def monitor_udp_messages(duration=30):
    """Monitor UDP message reception"""
    base_url = "http://localhost:8000/api/v1/mavlink"
    
    print(f"\nStarting UDP message monitoring ({duration} seconds)...")
    print("Please ensure UDP test tool is sending data to port 14550")
    print("-" * 50)
    
    start_time = time.time()
    last_count = 0
    
    while time.time() - start_time < duration:
        try:
            response = requests.get(f"{base_url}/udp/messages?limit=1000")
            if response.status_code == 200:
                messages = response.json()
                current_count = messages['total']
                
                if current_count > last_count:
                    new_messages = current_count - last_count
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Received {new_messages} new messages, total: {current_count}")
                    last_count = current_count
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Waiting for new messages... (total: {current_count})")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Failed to get messages")
                
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Error: {e}")
        
        time.sleep(2)  # Check every 2 seconds
    
    print("-" * 50)
    print("Monitoring ended")


def main():
    """Main function"""
    print("UDP Receiver Test Tool")
    print("Please ensure service is started: python start.py")
    print()
    
    while True:
        print("\nSelect operation:")
        print("1. Test UDP receiver status")
        print("2. Monitor UDP message reception")
        print("3. Exit")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            test_udp_receiver()
        elif choice == "2":
            duration = input("Monitoring duration (seconds, default 30): ").strip()
            duration = int(duration) if duration.isdigit() else 30
            monitor_udp_messages(duration)
        elif choice == "3":
            print("Exiting test tool")
            break
        else:
            print("Invalid choice, please try again")


if __name__ == "__main__":
    main()

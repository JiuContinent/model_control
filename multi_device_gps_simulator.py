#!/usr/bin/env python3
"""
Multi-Device GPS Simulator - Simulate multiple devices with realistic GPS data
"""
import time
import random
import math
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from app.services.mqtt_service import mqtt_service
from app.mavlink.advanced_parser import AdvancedMavlinkParser

class MultiDeviceGPSSimulator:
    """Multi-device GPS simulator with realistic movement patterns"""
    
    def __init__(self):
        self.devices = {}
        self.parser = AdvancedMavlinkParser()
        self.mqtt_connected = False
        
        # Device configurations based on logs
        self.device_configs = [
            {
                "name": "Drone Alpha",
                "system_id": 9,
                "component_id": 1,
                "client_address": "27.11.11.181:58711",
                "base_lat": 32.050192,
                "base_lon": 119.068108,
                "base_alt": 62.2,
                "color": "blue"
            },
            {
                "name": "Drone Beta", 
                "system_id": 10,
                "component_id": 1,
                "client_address": "27.11.11.182:58712",
                "base_lat": 32.051000,
                "base_lon": 119.069000,
                "base_alt": 75.0,
                "color": "red"
            },
            {
                "name": "Drone Gamma",
                "system_id": 11,
                "component_id": 1,
                "client_address": "27.11.11.183:58713",
                "base_lat": 32.049000,
                "base_lon": 119.067000,
                "base_alt": 45.0,
                "color": "green"
            }
        ]
        
        # Movement patterns
        self.movement_patterns = [
            {"name": "Hover", "type": "stationary", "speed": 0, "alt_change": 0},
            {"name": "Slow Patrol", "type": "linear", "speed": 0.00005, "alt_change": 0.02},
            {"name": "Medium Patrol", "type": "linear", "speed": 0.0001, "alt_change": 0.05},
            {"name": "Fast Patrol", "type": "linear", "speed": 0.0002, "alt_change": 0.1},
            {"name": "Circular", "type": "circular", "speed": 0.0001, "alt_change": 0.03},
            {"name": "Altitude Change", "type": "vertical", "speed": 0.00002, "alt_change": 0.3},
            {"name": "Search Pattern", "type": "search", "speed": 0.00008, "alt_change": 0.04}
        ]
        
        # GPS fix patterns from logs
        self.fix_types = [1, 11, 33, 44, 155, 171, 187, 196, 218, 239, 248]
        
    async def start_mqtt(self):
        """Start MQTT service"""
        try:
            await mqtt_service.start()
            self.mqtt_connected = True
            print("? MQTT service connected")
        except Exception as e:
            print(f"? MQTT connection failed: {e}")
            self.mqtt_connected = False
    
    def initialize_devices(self):
        """Initialize all devices"""
        for config in self.device_configs:
            device_id = f"device_{config['system_id']}_{config['component_id']}_{config['client_address'].replace('.', '_').replace(':', '_')}"
            
            self.devices[device_id] = {
                "config": config,
                "current_lat": config["base_lat"],
                "current_lon": config["base_lon"], 
                "current_alt": config["base_alt"],
                "direction": random.uniform(0, 360),
                "pattern_index": random.randint(0, len(self.movement_patterns) - 1),
                "pattern_start_time": time.time(),
                "sequence": 0,
                "message_count": 0,
                "gps_fix_count": 0
            }
            
            print(f"? Initialized {config['name']} ({device_id})")
    
    def update_device_position(self, device_id: str):
        """Update device position based on movement pattern"""
        device = self.devices[device_id]
        config = device["config"]
        pattern = self.movement_patterns[device["pattern_index"]]
        
        # Change pattern every 30 seconds
        if time.time() - device["pattern_start_time"] > 30:
            device["pattern_index"] = (device["pattern_index"] + 1) % len(self.movement_patterns)
            device["pattern_start_time"] = time.time()
            pattern = self.movement_patterns[device["pattern_index"]]
            print(f"[{config['name']}] Switching to: {pattern['name']}")
        
        # Apply movement based on pattern type
        if pattern["type"] == "stationary":
            # No movement
            pass
        elif pattern["type"] == "linear":
            # Linear movement
            lat_change = pattern["speed"] * math.cos(math.radians(device["direction"]))
            lon_change = pattern["speed"] * math.sin(math.radians(device["direction"]))
            
            device["current_lat"] += lat_change
            device["current_lon"] += lon_change
            
            # Gradually change direction
            device["direction"] += random.uniform(-5, 5)
            device["direction"] = device["direction"] % 360
            
        elif pattern["type"] == "circular":
            # Circular movement around base position
            radius = 0.001  # degrees
            angle = math.radians(device["direction"])
            device["current_lat"] = config["base_lat"] + radius * math.cos(angle)
            device["current_lon"] = config["base_lon"] + radius * math.sin(angle)
            device["direction"] += 10  # degrees per update
            
        elif pattern["type"] == "vertical":
            # Vertical movement
            lat_change = pattern["speed"] * math.cos(math.radians(device["direction"]))
            lon_change = pattern["speed"] * math.sin(math.radians(device["direction"]))
            
            device["current_lat"] += lat_change
            device["current_lon"] += lon_change
            
        elif pattern["type"] == "search":
            # Search pattern (figure-8)
            t = time.time() * 0.1
            radius = 0.0005
            device["current_lat"] = config["base_lat"] + radius * math.sin(t)
            device["current_lon"] = config["base_lon"] + radius * math.sin(t) * math.cos(t)
        
        # Update altitude
        alt_change = random.uniform(-pattern["alt_change"], pattern["alt_change"])
        device["current_alt"] += alt_change
        
        # Keep values in reasonable ranges
        device["current_alt"] = max(10.0, min(1000.0, device["current_alt"]))
        device["current_lat"] = max(-90.0, min(90.0, device["current_lat"]))
        device["current_lon"] = max(-180.0, min(180.0, device["current_lon"]))
    
    def generate_gps_data(self, device_id: str) -> Dict[str, Any]:
        """Generate GPS data for a specific device"""
        device = self.devices[device_id]
        config = device["config"]
        
        # Update position
        self.update_device_position(device_id)
        
        # Generate GPS data
        gps_data = {
            "device_id": device_id,
            "system_id": config["system_id"],
            "component_id": config["component_id"],
            "client_address": config["client_address"],
            "device_type": "drone",
            "device_name": config["name"],
            "latitude": round(device["current_lat"], 6),
            "longitude": round(device["current_lon"], 6),
            "altitude": round(device["current_alt"], 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fix_type": random.choice(self.fix_types),
            "satellites_visible": random.randint(0, 12),
            "ground_speed": round(random.uniform(0.0, 15.0), 1),
            "course_over_ground": round(device["direction"], 1),
            "message_sequence": device["sequence"],
            "message_type": "GPS_RAW_INT",
            "device_stats": {
                "message_count": device["message_count"],
                "gps_fix_count": device["gps_fix_count"],
                "first_seen": (datetime.now(timezone.utc) - timezone.timedelta(minutes=5)).isoformat(),
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            "raw_data": {
                "time_usec": int(time.time() * 1000000),
                "fix_type": random.choice(self.fix_types),
                "lat": round(device["current_lat"], 6),
                "lon": round(device["current_lon"], 6),
                "alt": round(device["current_alt"], 1),
                "raw_lat": int(device["current_lat"] * 1e7),
                "raw_lon": int(device["current_lon"] * 1e7),
                "raw_alt": int(device["current_alt"] * 1000),
                "payload_length": 44
            }
        }
        
        # Update device counters
        device["sequence"] += 1
        device["message_count"] += 1
        device["gps_fix_count"] += 1
        
        return gps_data
    
    def generate_mavlink_packet(self, device_id: str) -> bytes:
        """Generate MAVLink v2 GPS_RAW_INT packet for device"""
        device = self.devices[device_id]
        config = device["config"]
        
        # MAVLink v2 header: [FD][LEN][INCOMPAT][COMPAT][SEQ][SYSID][COMPID][MSGID(3)]
        header = bytearray([
            0xFD,  # MAVLink v2 signature
            0x2C,  # Payload length (44 bytes)
            0x00,  # Incompatibility flags
            0x00,  # Compatibility flags
            device["sequence"] & 0xFF,  # Sequence
            config["system_id"],  # System ID
            config["component_id"],  # Component ID
            0x18, 0x00, 0x00  # Message ID 24 (GPS_RAW_INT) - little endian
        ])
        
        # GPS payload data (44 bytes)
        time_usec = int(time.time() * 1000000)
        fix_type = random.choice(self.fix_types)
        lat_raw = int(device["current_lat"] * 1e7)
        lon_raw = int(device["current_lon"] * 1e7)
        alt_raw = int(device["current_alt"] * 1000)
        
        # Pack payload data
        import struct
        payload = struct.pack('<QBiiihhhhBiiiiH',
            time_usec,      # time_usec (8 bytes)
            fix_type,       # fix_type (1 byte)
            lat_raw,        # lat (4 bytes)
            lon_raw,        # lon (4 bytes)
            alt_raw,        # alt (4 bytes)
            100,            # eph (2 bytes)
            100,            # epv (2 bytes)
            0,              # vel (2 bytes)
            0,              # cog (2 bytes)
            0,              # satellites_visible (1 byte)
            0,              # alt_ellipsoid (4 bytes)
            0,              # h_acc (4 bytes)
            0,              # v_acc (4 bytes)
            0,              # vel_acc (4 bytes)
            0               # hdg_acc (2 bytes)
        )
        
        # Combine header and payload
        packet = header + payload
        
        # Add CRC (simplified)
        packet += b'\x00\x00'
        
        return bytes(packet)
    
    async def simulate_device(self, device_id: str, interval_seconds: float = 2.0):
        """Simulate a single device"""
        device = self.devices[device_id]
        config = device["config"]
        
        while True:
            try:
                # Generate GPS data
                gps_data = self.generate_gps_data(device_id)
                
                # Generate MAVLink packet
                packet = self.generate_mavlink_packet(device_id)
                
                # Parse packet using our parser
                result = self.parser.parse_packet(packet, config["client_address"])
                
                # Print device status
                pattern = self.movement_patterns[device["pattern_index"]]
                print(f"[{config['name']}] {pattern['name']}: ({gps_data['latitude']:.6f}, {gps_data['longitude']:.6f}) Alt: {gps_data['altitude']:.1f}m")
                
                # Publish to MQTT if connected
                if self.mqtt_connected and result and result['message_type'] == 'GPS_RAW_INT':
                    parsed_data = result.get('parsed_data', {})
                    if 'lat' in parsed_data and 'lon' in parsed_data:
                        lat = parsed_data['lat']
                        lon = parsed_data['lon']
                        alt = parsed_data.get('alt', 0.0)
                        await mqtt_service.publish_gps_data(gps_data)
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                print(f"Error simulating {config['name']}: {e}")
                await asyncio.sleep(interval_seconds)
    
    async def run_simulation(self, duration_seconds: int = 300):
        """Run multi-device simulation"""
        print("=== Multi-Device GPS Simulator ===")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Devices: {len(self.device_configs)}")
        print()
        
        # Initialize devices
        self.initialize_devices()
        
        # Start MQTT
        await self.start_mqtt()
        
        # Create tasks for all devices
        tasks = []
        for device_id in self.devices.keys():
            # Different intervals for different devices
            interval = random.uniform(1.5, 3.0)
            task = asyncio.create_task(self.simulate_device(device_id, interval))
            tasks.append(task)
        
        # Run simulation for specified duration
        try:
            await asyncio.sleep(duration_seconds)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
        
        # Cancel all tasks
        for task in tasks:
            task.cancel()
        
        # Stop MQTT
        if self.mqtt_connected:
            await mqtt_service.stop()
        
        print("=== Simulation Complete ===")


async def main():
    """Main function"""
    simulator = MultiDeviceGPSSimulator()
    await simulator.run_simulation(duration_seconds=120)  # 2 minutes


if __name__ == "__main__":
    asyncio.run(main())


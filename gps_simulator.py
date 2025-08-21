#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPS Data Simulator - Generate realistic GPS data based on log patterns
"""
import time
import random
import math
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple

class GPSSimulator:
    """GPS data simulator based on real log patterns"""
    
    def __init__(self):
        # Base coordinates from logs
        self.base_lat = 32.050192
        self.base_lon = 119.068108
        self.base_alt = 62.2
        
        # Movement patterns
        self.current_lat = self.base_lat
        self.current_lon = self.base_lon
        self.current_alt = self.base_alt
        
        # Movement parameters
        self.speed = 0.0001  # degrees per update
        self.altitude_change = 0.1  # meters per update
        self.direction = 0  # degrees (0-360)
        self.direction_change = 5  # degrees per update
        
        # GPS fix patterns from logs
        self.fix_types = [1, 11, 33, 44, 155, 171, 187, 196, 218, 239, 248]
        self.satellites_range = (0, 12)
        
        # System configuration
        self.system_id = 9
        self.component_id = 1
        self.client_address = "27.11.11.181:58711"
        self.sequence = 0
        
        # Movement scenarios
        self.scenarios = [
            {"name": "Stationary", "speed": 0, "alt_change": 0},
            {"name": "Slow Movement", "speed": 0.00005, "alt_change": 0.05},
            {"name": "Medium Movement", "speed": 0.0001, "alt_change": 0.1},
            {"name": "Fast Movement", "speed": 0.0002, "alt_change": 0.2},
            {"name": "Altitude Change", "speed": 0.00005, "alt_change": 0.5},
            {"name": "Circular Pattern", "speed": 0.0001, "alt_change": 0.05}
        ]
        self.current_scenario = 0
        self.scenario_duration = 30  # seconds per scenario
        
    def generate_gps_data(self) -> Dict[str, Any]:
        """Generate realistic GPS data based on log patterns"""
        # Update position based on current scenario
        self._update_position()
        
        # Generate realistic GPS data
        gps_data = {
            "device_id": f"device_{self.system_id}_{self.component_id}_{self.client_address.replace('.', '_').replace(':', '_')}",
            "system_id": self.system_id,
            "component_id": self.component_id,
            "client_address": self.client_address,
            "device_type": "drone",
            "latitude": round(self.current_lat, 6),
            "longitude": round(self.current_lon, 6),
            "altitude": round(self.current_alt, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fix_type": random.choice(self.fix_types),
            "satellites_visible": random.randint(*self.satellites_range),
            "ground_speed": round(random.uniform(0.0, 15.0), 1),
            "course_over_ground": round(random.uniform(0.0, 360.0), 1),
            "message_sequence": self.sequence,
            "message_type": "GPS_RAW_INT",
            "device_stats": {
                "message_count": self.sequence + 1,
                "gps_fix_count": self.sequence + 1,
                "first_seen": (datetime.now(timezone.utc) - timezone.timedelta(minutes=5)).isoformat(),
                "last_seen": datetime.now(timezone.utc).isoformat()
            },
            "raw_data": {
                "time_usec": int(time.time() * 1000000),
                "fix_type": random.choice(self.fix_types),
                "lat": round(self.current_lat, 6),
                "lon": round(self.current_lon, 6),
                "alt": round(self.current_alt, 1),
                "raw_lat": int(self.current_lat * 1e7),
                "raw_lon": int(self.current_lon * 1e7),
                "raw_alt": int(self.current_alt * 1000),
                "payload_length": 44
            }
        }
        
        self.sequence += 1
        return gps_data
    
    def _update_position(self):
        """Update position based on current scenario"""
        scenario = self.scenarios[self.current_scenario]
        
        # Update scenario every scenario_duration seconds
        if int(time.time()) % self.scenario_duration == 0:
            self.current_scenario = (self.current_scenario + 1) % len(self.scenarios)
            scenario = self.scenarios[self.current_scenario]
            print(f"[SIM] Switching to scenario: {scenario['name']}")
        
        # Apply movement based on scenario
        if scenario['name'] == "Circular Pattern":
            # Circular movement
            radius = 0.001  # degrees
            angle = math.radians(self.direction)
            self.current_lat = self.base_lat + radius * math.cos(angle)
            self.current_lon = self.base_lon + radius * math.sin(angle)
            self.direction += 10  # degrees per update
        else:
            # Linear movement
            lat_change = scenario['speed'] * math.cos(math.radians(self.direction))
            lon_change = scenario['speed'] * math.sin(math.radians(self.direction))
            
            self.current_lat += lat_change
            self.current_lon += lon_change
            
            # Gradually change direction
            self.direction += random.uniform(-self.direction_change, self.direction_change)
            self.direction = self.direction % 360
        
        # Update altitude
        self.current_alt += random.uniform(-scenario['alt_change'], scenario['alt_change'])
        
        # Keep altitude reasonable
        self.current_alt = max(10.0, min(1000.0, self.current_alt))
        
        # Keep coordinates in reasonable range
        self.current_lat = max(-90.0, min(90.0, self.current_lat))
        self.current_lon = max(-180.0, min(180.0, self.current_lon))
    
    def generate_mavlink_packet(self) -> bytes:
        """Generate MAVLink v2 GPS_RAW_INT packet"""
        # MAVLink v2 header: [FD][LEN][INCOMPAT][COMPAT][SEQ][SYSID][COMPID][MSGID(3)]
        header = bytearray([
            0xFD,  # MAVLink v2 signature
            0x2C,  # Payload length (44 bytes)
            0x00,  # Incompatibility flags
            0x00,  # Compatibility flags
            self.sequence & 0xFF,  # Sequence
            self.system_id,  # System ID
            self.component_id,  # Component ID
            0x18, 0x00, 0x00  # Message ID 24 (GPS_RAW_INT) - little endian
        ])
        
        # GPS payload data (44 bytes)
        time_usec = int(time.time() * 1000000)
        fix_type = random.choice(self.fix_types)
        lat_raw = int(self.current_lat * 1e7)
        lon_raw = int(self.current_lon * 1e7)
        alt_raw = int(self.current_alt * 1000)
        
        # Pack payload data
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
        
        # Add CRC (simplified - in real implementation you'd calculate proper CRC)
        packet += b'\x00\x00'
        
        return bytes(packet)
    
    def get_scenario_info(self) -> Dict[str, Any]:
        """Get current scenario information"""
        scenario = self.scenarios[self.current_scenario]
        return {
            "current_scenario": scenario['name'],
            "scenario_index": self.current_scenario,
            "total_scenarios": len(self.scenarios),
            "scenario_duration": self.scenario_duration,
            "current_position": {
                "latitude": round(self.current_lat, 6),
                "longitude": round(self.current_lon, 6),
                "altitude": round(self.current_alt, 1)
            },
            "movement": {
                "speed": scenario['speed'],
                "direction": round(self.direction, 1),
                "altitude_change": scenario['alt_change']
            }
        }


# Import struct for packet generation
import struct

def simulate_gps_stream(duration_seconds: int = 60, interval_seconds: float = 1.0):
    """Simulate GPS data stream for specified duration"""
    simulator = GPSSimulator()
    
    print(f"=== GPS Data Simulator ===")
    print(f"Duration: {duration_seconds} seconds")
    print(f"Interval: {interval_seconds} seconds")
    print(f"Device: {simulator.client_address}")
    print()
    
    start_time = time.time()
    packet_count = 0
    
    try:
        while time.time() - start_time < duration_seconds:
            # Generate GPS data
            gps_data = simulator.generate_gps_data()
            
            # Print GPS data
            print(f"[{datetime.now().strftime('%H:%M:%S')}] GPS Update #{packet_count + 1}")
            print(f"  Position: ({gps_data['latitude']:.6f}, {gps_data['longitude']:.6f})")
            print(f"  Altitude: {gps_data['altitude']:.1f}m")
            print(f"  Fix: {gps_data['fix_type']}, Sats: {gps_data['satellites_visible']}")
            print(f"  Speed: {gps_data['ground_speed']:.1f} m/s, Course: {gps_data['course_over_ground']:.1f}бу")
            
            # Show scenario info
            scenario_info = simulator.get_scenario_info()
            print(f"  Scenario: {scenario_info['current_scenario']}")
            print()
            
            packet_count += 1
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped by user")
    
    print(f"=== Simulation Complete ===")
    print(f"Total packets: {packet_count}")
    print(f"Duration: {time.time() - start_time:.1f} seconds")
    print(f"Average rate: {packet_count / (time.time() - start_time):.1f} packets/second")


if __name__ == "__main__":
    # Run GPS simulation for 60 seconds with 1-second intervals
    simulate_gps_stream(duration_seconds=60, interval_seconds=1.0)

"""
UDP Receiver for MAVLink data
Automatically receives MAVLink packets from UDP clients
"""
import asyncio
import socket
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import base64

from app.mavlink.advanced_parser import AdvancedMavlinkParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MavlinkUdpReceiver:
    """UDP receiver for MAVLink data"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 14550):
        self.host = host
        self.port = port
        self.parser = AdvancedMavlinkParser()
        self.is_running = False
        self.socket = None
        self.messages = []
        self.sessions = []
        self.task = None
        
    async def start(self):
        """Start UDP receiver"""
        if self.is_running:
            logger.info("UDP receiver is already running")
            return
            
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.setblocking(False)
            
            self.is_running = True
            logger.info(f"UDP receiver started on {self.host}:{self.port}")
            
            # Start receiving loop
            self.task = asyncio.create_task(self._receive_loop())
            
        except Exception as e:
            logger.error(f"Failed to start UDP receiver: {e}")
            raise
    
    async def stop(self):
        """Stop UDP receiver"""
        if not self.is_running:
            return
            
        self.is_running = False
        
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        if self.socket:
            self.socket.close()
            
        logger.info("UDP receiver stopped")
    
    async def _receive_loop(self):
        """Main receive loop"""
        loop = asyncio.get_event_loop()
        
        while self.is_running:
            try:
                # Use asyncio to wait for data
                data, addr = await loop.run_in_executor(
                    None, 
                    self._receive_data
                )
                
                if data:
                    await self._process_packet(data, addr)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(0.1)
    
    def _receive_data(self) -> tuple:
        """Receive data from socket (blocking)"""
        try:
            data, addr = self.socket.recvfrom(1024)
            return data, addr
        except BlockingIOError:
            return None, None
        except Exception as e:
            logger.error(f"Socket receive error: {e}")
            return None, None
    
    async def _process_packet(self, data: bytes, addr: tuple):
        """Process received MAVLink packet"""
        try:
            client_address = f"{addr[0]}:{addr[1]}"

            # Debug: Log raw data occasionally
            if not hasattr(self, '_debug_counter'):
                self._debug_counter = 0
            self._debug_counter += 1
            
            if self._debug_counter % 50 == 1:  # Log every 50th packet
                logger.info(f"DEBUG: Received {len(data)} bytes from {client_address}")
                logger.info(f"DEBUG: Raw data (first 20 bytes): {data[:20].hex()}")
                if len(data) >= 10:
                    logger.info(f"DEBUG: First byte: 0x{data[0]:02x}, Payload length: {data[1]}")

            # Split possible multiple MAVLink v2 packets within this UDP datagram
            packets = self._split_mavlink_packets(data)

            if not packets:
                # Only log parse failures occasionally to reduce spam
                if hasattr(self, '_parse_fail_count'):
                    self._parse_fail_count += 1
                else:
                    self._parse_fail_count = 1
                if self._parse_fail_count % 100 == 0:
                    logger.warning(f"Failed to parse {self._parse_fail_count} MAVLink packets from {client_address}")
                    if self._parse_fail_count == 100:  # First failure, show debug info
                        logger.info(f"DEBUG: Sample failed data: {data[:50].hex()}")
                return

            for pkt in packets:
                message = self.parser.parse_packet(pkt, client_address)
                if not message:
                    if hasattr(self, '_parse_fail_count'):
                        self._parse_fail_count += 1
                    else:
                        self._parse_fail_count = 1
                    continue

                # Store message
                self.messages.append(message)

                # Update or create session
                session_key = f"{message['system_id']}_{client_address}"
                existing_session = next(
                    (s for s in self.sessions if s['key'] == session_key),
                    None
                )

                if existing_session:
                    existing_session['last_seen'] = message['timestamp']
                    existing_session['message_count'] += 1
                else:
                    self.sessions.append({
                        'key': session_key,
                        'system_id': message['system_id'],
                        'client_address': client_address,
                        'first_seen': message['timestamp'],
                        'last_seen': message['timestamp'],
                        'message_count': 1,
                        'is_active': True
                    })

            # Log aggregated results occasionally
            if hasattr(self, '_parse_fail_count') and self._parse_fail_count and self._parse_fail_count % 100 == 0:
                logger.warning(f"Failed to parse {self._parse_fail_count} MAVLink packets from {client_address}")

        except Exception as e:
            logger.error(f"Error processing packet: {e}")

    def _split_mavlink_packets(self, data: bytes) -> list:
        """Scan a UDP datagram for one or more MAVLink v2 packets and return list of slices.
        Handle both complete and truncated packets.
        """
        packets = []
        i = 0
        length = len(data)
        
        while i + 10 <= length:
            # Find next v2 STX
            if data[i] != 0xFD:
                i += 1
                continue
                
            # Need at least header
            if i + 10 > length:
                break
                
            payload_len = data[i + 1]
            # header is 10 bytes, payload follows
            total_no_crc = 10 + payload_len
            
            if i + total_no_crc <= length:
                # Complete packet
                packets.append(data[i:i + total_no_crc])
                i += total_no_crc
            else:
                # Truncated packet - include what we have
                if i + 10 <= length:
                    packets.append(data[i:length])
                break
                
        return packets
    
    def get_messages(self, limit: int = 100) -> list:
        """Get stored messages"""
        return self.messages[-limit:] if limit > 0 else self.messages
    
    def get_sessions(self) -> list:
        """Get active sessions"""
        return self.sessions
    
    def get_stats(self) -> Dict[str, Any]:
        """Get receiver statistics"""
        return {
            "is_running": self.is_running,
            "host": self.host,
            "port": self.port,
            "parser_stats": self.parser.get_stats(),
            "stored_messages": len(self.messages),
            "active_sessions": len(self.sessions),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global UDP receiver instance
udp_receiver = MavlinkUdpReceiver()


async def start_udp_receiver():
    """Start the UDP receiver"""
    await udp_receiver.start()


async def stop_udp_receiver():
    """Stop the UDP receiver"""
    await udp_receiver.stop()


def get_udp_receiver():
    """Get the UDP receiver instance"""
    return udp_receiver

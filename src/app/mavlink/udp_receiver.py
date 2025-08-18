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

from app.mavlink.simple_parser import SimpleMavlinkParser

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MavlinkUdpReceiver:
    """UDP receiver for MAVLink data"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 14550):
        self.host = host
        self.port = port
        self.parser = SimpleMavlinkParser()
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
            logger.info(f"Received {len(data)} bytes from {client_address}")
            
            # Parse MAVLink packet
            message = self.parser.parse_packet(data, client_address)
            
            if message:
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
                
                logger.info(f"Parsed MAVLink message: ID={message['message_id']}, "
                          f"System={message['system_id']}, "
                          f"Component={message['component_id']}")
            else:
                logger.warning(f"Failed to parse MAVLink packet from {client_address}")
                
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
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

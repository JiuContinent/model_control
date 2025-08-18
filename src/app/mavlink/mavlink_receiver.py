"""
MAVLink TCP Receiver Service
Receives MAVLink binary data over TCP and stores it in MongoDB
"""
import asyncio
import socket
from datetime import datetime, timezone
from typing import Dict, Set, Optional
import logging

from app.mavlink.mavlink_parser import MavlinkParser
from app.models.mavlink_models import MavlinkMessage, MavlinkSession, MavlinkStatistics
from app.db.mongo_multi import use_source

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MavlinkReceiver:
    """MAVLink TCP receiver service"""
    
    def __init__(self):
        self.server: Optional[asyncio.Server] = None
        self.port: Optional[int] = None
        self.is_running_flag = False
        self.start_time: Optional[datetime] = None
        self.active_connections: Set[asyncio.StreamReader] = set()
        self.total_messages_received = 0
        self.parser = MavlinkParser()
        
        # Session tracking
        self.sessions: Dict[int, MavlinkSession] = {}
        self.daily_stats: Dict[str, MavlinkStatistics] = {}
    
    def is_running(self) -> bool:
        """Check if receiver is running"""
        return self.is_running_flag
    
    async def start(self, port: int = 5760):
        """Start MAVLink receiver on specified port"""
        if self.is_running():
            logger.warning("Receiver is already running")
            return
        
        try:
            self.server = await asyncio.start_server(
                self._handle_client, '0.0.0.0', port
            )
            self.port = port
            self.is_running_flag = True
            self.start_time = datetime.now(timezone.utc)
            
            logger.info(f"MAVLink receiver started on port {port}")
            
            # Start background tasks
            asyncio.create_task(self._update_statistics())
            
        except Exception as e:
            logger.error(f"Failed to start receiver: {e}")
            raise
    
    async def stop(self):
        """Stop MAVLink receiver"""
        if not self.is_running():
            logger.warning("Receiver is not running")
            return
        
        try:
            # Close all client connections
            for reader in list(self.active_connections):
                try:
                    reader.close()
                except Exception as e:
                    logger.error(f"Error closing client connection: {e}")
            
            self.active_connections.clear()
            
            # Close server
            if self.server:
                self.server.close()
                await self.server.wait_closed()
            
            self.is_running_flag = False
            self.port = None
            self.start_time = None
            
            logger.info("MAVLink receiver stopped")
            
        except Exception as e:
            logger.error(f"Error stopping receiver: {e}")
            raise
    
    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming client connection"""
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New client connected: {client_addr}")
        
        self.active_connections.add(reader)
        
        try:
            buffer = bytearray()
            
            while True:
                # Read data from client
                data = await reader.read(1024)
                if not data:
                    break
                
                buffer.extend(data)
                
                # Process complete packets
                while len(buffer) >= 8:  # Minimum packet size
                    packet_length = self._get_packet_length(buffer)
                    if packet_length is None or len(buffer) < packet_length:
                        break
                    
                    # Extract complete packet
                    packet = buffer[:packet_length]
                    buffer = buffer[packet_length:]
                    
                    # Process packet
                    await self._process_packet(packet, client_addr)
                    
        except Exception as e:
            logger.error(f"Error handling client {client_addr}: {e}")
        
        finally:
            self.active_connections.discard(reader)
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            
            logger.info(f"Client disconnected: {client_addr}")
    
    def _get_packet_length(self, buffer: bytearray) -> Optional[int]:
        """Get packet length from buffer"""
        if len(buffer) < 8:
            return None
        
        # Check MAVLink v1 vs v2
        if buffer[0] == 0xFE:  # MAVLink v1
            return buffer[1] + 8
        elif buffer[0] == 0xFD:  # MAVLink v2
            return buffer[1] + 10
        else:
            return None
    
    async def _process_packet(self, packet: bytes, client_addr):
        """Process MAVLink packet"""
        try:
            # Parse packet
            parsed = self.parser.parse_packet(packet)
            if not parsed:
                logger.warning(f"Failed to parse packet from {client_addr}")
                return
            
            # Create message record
            message = MavlinkMessage(
                message_id=parsed['message_id'],
                system_id=parsed['system_id'],
                component_id=parsed['component_id'],
                sequence=parsed['sequence'],
                payload=parsed['payload'],
                parsed_data=parsed.get('parsed_data', {}),
                timestamp=datetime.now(timezone.utc),
                client_address=str(client_addr),
                packet_length=len(packet),
                is_valid=parsed.get('is_valid', True)
            )
            
            # Save to database
            async with use_source("mavlink"):
                await message.save()
            
            # Update session tracking
            await self._update_session(parsed['system_id'], client_addr)
            
            # Update statistics
            self.total_messages_received += 1
            
            logger.debug(f"Processed packet: {parsed['message_id']} from system {parsed['system_id']}")
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    async def _update_session(self, system_id: int, client_addr):
        """Update session tracking for system"""
        try:
            session_key = f"{system_id}_{client_addr}"
            now = datetime.now(timezone.utc)
            
            if session_key not in self.sessions:
                # Create new session
                session = MavlinkSession(
                    system_id=system_id,
                    client_address=str(client_addr),
                    first_seen=now,
                    last_seen=now,
                    message_count=1,
                    is_active=True
                )
                
                async with use_source("mavlink"):
                    await session.save()
                
                self.sessions[session_key] = session
            else:
                # Update existing session
                session = self.sessions[session_key]
                session.last_seen = now
                session.message_count += 1
                session.is_active = True
                
                async with use_source("mavlink"):
                    await session.save()
                    
        except Exception as e:
            logger.error(f"Error updating session: {e}")
    
    async def _update_statistics(self):
        """Update daily statistics"""
        while self.is_running():
            try:
                await asyncio.sleep(60)  # Update every minute
                
                now = datetime.now(timezone.utc)
                today = now.date().isoformat()
                
                if today not in self.daily_stats:
                    # Create new daily statistics
                    stats = MavlinkStatistics(
                        date=now.date(),
                        total_messages=0,
                        unique_systems=0,
                        active_sessions=0,
                        last_updated=now
                    )
                    
                    async with use_source("mavlink"):
                        await stats.save()
                    
                    self.daily_stats[today] = stats
                
                # Update current day statistics
                stats = self.daily_stats[today]
                stats.total_messages = self.total_messages_received
                stats.unique_systems = len(set(s.system_id for s in self.sessions.values()))
                stats.active_sessions = len([s for s in self.sessions.values() if s.is_active])
                stats.last_updated = now
                
                async with use_source("mavlink"):
                    await stats.save()
                    
            except Exception as e:
                logger.error(f"Error updating statistics: {e}")
    
    async def get_status(self) -> Dict:
        """Get receiver status"""
        return {
            "is_running": self.is_running(),
            "port": self.port,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "active_connections": len(self.active_connections),
            "total_messages_received": self.total_messages_received,
            "active_sessions": len([s for s in self.sessions.values() if s.is_active]),
            "total_sessions": len(self.sessions)
        }


# Global receiver instance
mavlink_receiver = MavlinkReceiver()

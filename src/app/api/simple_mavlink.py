"""
Simple MAVLink API - Basic endpoints for testing
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional, Dict
import base64
from datetime import datetime, timezone

from app.mavlink.simple_parser import SimpleMavlinkParser
from app.mavlink.udp_receiver import get_udp_receiver, start_udp_receiver, stop_udp_receiver
from app.models.simple_models import MavlinkMessage

router = APIRouter(prefix="/mavlink", tags=["MAVLink"])

# Global parser instance
parser = SimpleMavlinkParser()

# In-memory storage for testing (HTTP API)
http_messages: List[Dict] = []
http_sessions: List[Dict] = []


@router.post("/parse")
async def parse_mavlink_data(data: str, client_address: str = "test_client"):
    """Parse MAVLink binary data (base64 encoded) - HTTP API"""
    try:
        # Decode base64 data
        binary_data = base64.b64decode(data)
        
        # Parse packet
        message = parser.parse_packet(binary_data, client_address)
        
        if message:
            # Store message
            http_messages.append(message)
            
            # Update or create session
            session_key = f"{message['system_id']}_{client_address}"
            existing_session = next((s for s in http_sessions if s['key'] == session_key), None)
            
            if existing_session:
                existing_session['last_seen'] = message['timestamp']
                existing_session['message_count'] += 1
            else:
                http_sessions.append({
                    'key': session_key,
                    'system_id': message['system_id'],
                    'client_address': client_address,
                    'first_seen': message['timestamp'],
                    'last_seen': message['timestamp'],
                    'message_count': 1,
                    'is_active': True
                })
            
            return {"status": "success", "message": message}
        else:
            raise HTTPException(status_code=400, detail="Invalid MAVLink packet")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing data: {str(e)}")


@router.post("/udp/start")
async def start_udp(background_tasks: BackgroundTasks):
    """Start UDP receiver"""
    try:
        background_tasks.add_task(start_udp_receiver)
        return {"status": "success", "message": "UDP receiver starting..."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start UDP receiver: {str(e)}")


@router.post("/udp/stop")
async def stop_udp():
    """Stop UDP receiver"""
    try:
        await stop_udp_receiver()
        return {"status": "success", "message": "UDP receiver stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop UDP receiver: {str(e)}")


@router.get("/udp/status")
async def udp_status():
    """Get UDP receiver status"""
    receiver = get_udp_receiver()
    return receiver.get_stats()


@router.get("/messages")
async def get_messages(limit: int = 100, source: str = "all"):
    """Get parsed MAVLink messages from specified source"""
    if source == "http":
        messages = http_messages
    elif source == "udp":
        receiver = get_udp_receiver()
        messages = receiver.get_messages(limit)
    else:  # "all"
        receiver = get_udp_receiver()
        udp_messages = receiver.get_messages(limit)
        all_messages = http_messages + udp_messages
        # Sort by timestamp and take the latest
        all_messages.sort(key=lambda x: x['timestamp'])
        messages = all_messages[-limit:] if limit > 0 else all_messages
    
    return {
        "total": len(messages),
        "source": source,
        "messages": messages[-limit:] if limit > 0 else messages
    }


@router.get("/sessions")
async def get_sessions(source: str = "all"):
    """Get active MAVLink sessions from specified source"""
    if source == "http":
        sessions = http_sessions
    elif source == "udp":
        receiver = get_udp_receiver()
        sessions = receiver.get_sessions()
    else:  # "all"
        receiver = get_udp_receiver()
        udp_sessions = receiver.get_sessions()
        # Merge sessions by key
        all_sessions = {}
        for session in http_sessions + udp_sessions:
            key = session['key']
            if key not in all_sessions:
                all_sessions[key] = session
            else:
                # Merge session data
                all_sessions[key]['message_count'] += session['message_count']
                if session['last_seen'] > all_sessions[key]['last_seen']:
                    all_sessions[key]['last_seen'] = session['last_seen']
        sessions = list(all_sessions.values())
    
    return {
        "total": len(sessions),
        "source": source,
        "sessions": sessions
    }


@router.get("/stats")
async def get_stats():
    """Get combined statistics from all sources"""
    receiver = get_udp_receiver()
    udp_stats = receiver.get_stats()
    
    return {
        "http_api": {
            "stored_messages": len(http_messages),
            "active_sessions": len(http_sessions),
            "parser_stats": parser.get_stats()
        },
        "udp_receiver": udp_stats,
        "combined": {
            "total_messages": len(http_messages) + len(receiver.get_messages()),
            "total_sessions": len(http_sessions) + len(receiver.get_sessions()),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }


@router.post("/test")
async def test_mavlink():
    """Test endpoint with sample MAVLink data"""
    # Sample MAVLink v2 packet (FD 11 00 00 86 01 01 4A 00 00 00 00 00 00 00 00 00 00 0A D7 A3 3C 6B 5B B8 3C 80 8B B9)
    sample_data = "FD 11 00 00 86 01 01 4A 00 00 00 00 00 00 00 00 00 00 0A D7 A3 3C 6B 5B B8 3C 80 8B B9"
    
    # Convert hex string to bytes
    hex_bytes = bytes.fromhex(sample_data.replace(" ", ""))
    base64_data = base64.b64encode(hex_bytes).decode('utf-8')
    
    # Parse the sample data
    return await parse_mavlink_data(base64_data, "test_client")

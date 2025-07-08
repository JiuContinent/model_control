# services/socketio_service.py
import socketio

# AsyncServer (async 模式) + ASGI 兼容 FastAPI
sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins="*")

# 可以根据你需求扩展用户房间/登录验证
connected_users = {}

@sio.event
async def connect(sid, environ):
    print(f"🔌 Connected: {sid}")
    connected_users[sid] = {}
    await sio.emit("system", {"message": f"User {sid} connected"}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"❌ Disconnected: {sid}")
    connected_users.pop(sid, None)

@sio.event
async def chat_message(sid, data):
    print(f"💬 Message from {sid}: {data}")
    # 广播给所有客户端
    await sio.emit("chat_message", data)

@sio.event
async def voice_message(sid, data):
    print(f"🔊 Voice message from {sid}: {data}")
    # data: { "from": "userA", "to": "userB", "url": "http://..." }
    await sio.emit("voice_message", data, to=data["to"])

# src/app/socketio_app/server.py
from socketio import AsyncServer, ASGIApp
from fastapi import FastAPI

# 1. 创建 AsyncServer，允许所有源（开发时可调整）
sio = AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    ping_interval=25,          # 心跳间隔（可选）
    ping_timeout=60,           # 心跳超时（可选）
)

# 2. 定义事件
@sio.event
async def connect(sid, environ):
    print(f"[Socket.IO] 客户端已连接: {sid}")

@sio.event
async def chat_message(sid, data):
    """
    文字聊天。
    data = { "from": "user1", "message": "hello" }
    """
    # 广播给所有客户端
    await sio.emit("chat_message", data)

@sio.event
async def voice_message(sid, data):
    """
    非实时语音消息通知。
    data = {
        "from": "user1",
        "to": "user2",
        "url": "https://your.cdn.com/voice/abc123.mp3"
    }
    """
    # 只发给指定接收者
    await sio.emit("voice_message", data, room=data["to"])

@sio.event
async def disconnect(sid):
    print(f"[Socket.IO] 客户端已断开: {sid}")

# 3. 将 FastAPI app 和 socketio 绑定，返回复合 ASGI 应用
def create_socket_app(app: FastAPI):
    """
    将 socketio 挂载到已有的 FastAPI 实例上，
    返回一个 ASGIApp，以便 uvicorn 引用统一启动。
    """
    return ASGIApp(sio, other_asgi_app=app)

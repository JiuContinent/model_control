# src/app/main.py
"""
应用主入口文件。
- 使用 `lifespan` 上下文管理器统一管理应用的启动和关闭事件。
- 根据 USE_MYSQL/USE_MONGO 开关有条件地初始化数据库，并对失败情况做捕获。
- 注册所有 API 路由。
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.config import settings
from app.db.mongo import init_mongo_db
from app.db.mysql import async_engine, close_mysql_connection
from app.api import  crud, ai
from app.socketio_app.server import create_socket_app
from fastapi.staticfiles import StaticFiles
from pathlib import Path
@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"--- Starting up {settings.PROJECT_NAME} ---")

    # 1. MySQL 初始化（可选）
    if settings.USE_MYSQL:
        try:
            print("→ Testing MySQL connection...")
            async with async_engine.connect() as conn:
                await conn.execute("SELECT 1")
            print("✅ MySQL connected.")
        except Exception as e:
            print(f"⚠️ MySQL 初始化失败，已跳过: {e!r}")

    # 2. MongoDB 初始化（可选）
    if settings.USE_MONGO:
        try:
            print("→ Initializing MongoDB...")
            await init_mongo_db()
            print("✅ MongoDB initialized.")
        except Exception as e:
            print(f"⚠️ MongoDB 初始化失败，已跳过: {e!r}")

    print(f"--- Lifespan startup complete ---")
    yield
    print(f"--- Shutting down {settings.PROJECT_NAME} ---")

    # 3. MySQL 关闭连接（可选）
    if settings.USE_MYSQL:
        try:
            await close_mysql_connection()
            print("✅ MySQL connection closed.")
        except Exception as e:
            print(f"⚠️ MySQL 关闭失败: {e!r}")

    print(f"--- Lifespan shutdown complete ---")


# 创建 FastAPI 实例，指定 lifespan 管理器
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    lifespan=lifespan,
)
BASE_DIR = Path(__file__).parent
app.include_router(crud.router, prefix="/api", tags=["CRUD (MySQL)"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Engine"])

app.mount("/static", StaticFiles(directory= BASE_DIR / "static"), name="static")


@app.get("/", tags=["Root"])
def read_root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

socket_app = create_socket_app(app)
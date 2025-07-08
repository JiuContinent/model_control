# src/app/api/upload.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings

router = APIRouter()

# 存放上传文件的本地目录
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    接收客户端上传的音频文件，保存后返回可访问 URL
    """
    # 只允许这些格式
    if not file.filename.lower().endswith((".mp3", ".wav", ".ogg")):
        raise HTTPException(400, "不支持的音频格式")

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # 异步写文件
    from aiofiles import open as aio_open
    async with aio_open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # 返回一个可以被客户端下载/播放的 URL
    # 假设你在 Uvicorn 启动时增加了 StaticFiles 挂载 /uploads
    url = f"{settings.BASE_URL}/uploads/{unique_name}"
    return JSONResponse({"url": url})

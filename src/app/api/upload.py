# src/app/api/upload.py
import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.config import settings

router = APIRouter()

# Local directory for uploaded files
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """
    Receive audio file uploaded by client, save and return accessible URL
    """
    # Only allow these formats
    if not file.filename.lower().endswith((".mp3", ".wav", ".ogg")):
        raise HTTPException(400, "Unsupported audio format")

    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_name)

    # Async write file
    from aiofiles import open as aio_open
    async with aio_open(file_path, "wb") as f:
        content = await file.read()
        await f.write(content)

    # Return a URL that can be downloaded/played by client
    # Assuming you added StaticFiles mount /uploads when starting Uvicorn
    url = f"{settings.BASE_URL}/uploads/{unique_name}"
    return JSONResponse({"url": url})

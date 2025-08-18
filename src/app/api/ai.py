from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
import aiofiles
import os
from pathlib import Path

from app.services.ai_service import ai_service
from app.core.exceptions import AIProcessingException
from app.core.constants import API_CONFIG
from loguru import logger

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/detect")
async def detect_objects(
    file: UploadFile = File(...),
    confidence: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45)
):
    """
    Single image object detection
    
    Args:
        file: Uploaded image file
        confidence: Confidence threshold
        iou_threshold: IoU threshold
        
    Returns:
        Detection result
    """
    try:
        # Validate file type
        if not any(file.filename.lower().endswith(ext) for ext in API_CONFIG["allowed_image_types"]):
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported types: {API_CONFIG['allowed_image_types']}"
            )
        
        # Validate file size
        if file.size > API_CONFIG["max_file_size"]:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds limit. Maximum size: {API_CONFIG['max_file_size'] // (1024*1024)}MB"
            )
        
        # Save uploaded file
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        file_path = upload_dir / file.filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Execute detection
        result = await ai_service.detect_objects(str(file_path))
        
        # Clean up temporary files
        try:
            os.remove(file_path)
        except:
            pass
        
        return JSONResponse(content=result)
        
    except AIProcessingException as e:
        logger.error(f"AI processing exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {e}")


@router.post("/detect-batch")
async def detect_batch(
    files: List[UploadFile] = File(...),
    confidence: Optional[float] = Form(0.5),
    iou_threshold: Optional[float] = Form(0.45)
):
    """
    Batch image object detection
    
    Args:
        files: List of uploaded image files
        confidence: Confidence threshold
        iou_threshold: IoU threshold
        
    Returns:
        Batch detection results
    """
    try:
        # Validate file count
        if len(files) > API_CONFIG["max_batch_size"]:
            raise HTTPException(
                status_code=400,
                detail=f"Batch processing file count exceeds limit. Maximum count: {API_CONFIG['max_batch_size']}"
            )
        
        # Validate file types and sizes
        image_paths = []
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        
        for file in files:
            if not any(file.filename.lower().endswith(ext) for ext in API_CONFIG["allowed_image_types"]):
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} type not supported"
                )
            
            if file.size > API_CONFIG["max_file_size"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} size exceeds limit"
                )
            
            # Save file
            file_path = upload_dir / file.filename
            async with aiofiles.open(file_path, 'wb') as f:
                content = await file.read()
                await f.write(content)
            image_paths.append(str(file_path))
        
        # Execute batch detection
        results = await ai_service.detect_batch(image_paths)
        
        # Clean up temporary files
        for file_path in image_paths:
            try:
                os.remove(file_path)
            except:
                pass
        
        return JSONResponse(content=results)
        
    except AIProcessingException as e:
        logger.error(f"AI processing exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Batch detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch detection failed: {e}")


@router.get("/model-info")
async def get_model_info():
    """
    Get model information
    
    Returns:
        Model configuration information
    """
    try:
        return ai_service.get_model_info()
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get model info: {e}")


@router.post("/detect-url")
async def detect_from_url(image_url: str):
    """
    Detect objects from URL
    
    Args:
        image_url: Image URL
        
    Returns:
        Detection result
    """
    try:
        # Here should implement logic to download image from URL
        # Temporarily return error
        raise HTTPException(
            status_code=501,
            detail="URL detection feature not implemented yet"
        )
    except Exception as e:
        logger.error(f"URL detection failed: {e}")
        raise HTTPException(status_code=500, detail=f"URL detection failed: {e}")


@router.get("/health")
async def ai_health_check():
    """
    AI service health check
    
    Returns:
        Service status
    """
    try:
        model_info = ai_service.get_model_info()
        return {
            "status": "healthy",
            "model_loaded": model_info["model_name"] is not None,
            "model_name": model_info["model_name"],
            "timestamp": "2024-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"AI health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

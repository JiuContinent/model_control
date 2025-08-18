"""
File processing utilities
"""
import os
import hashlib
import uuid
from pathlib import Path
from typing import List, Optional
from loguru import logger


def ensure_directory(directory: str) -> None:
    """Ensure directory exists"""
    Path(directory).mkdir(parents=True, exist_ok=True)


def calculate_file_hash(file_path: str) -> str:
    """Calculate file MD5 hash value"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def save_uploaded_file(file_content: bytes, filename: str, upload_dir: str) -> str:
    """Save uploaded file"""
    ensure_directory(upload_dir)
    
    # Generate unique filename
    file_ext = Path(filename).suffix
    unique_name = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_dir, unique_name)
    
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
        logger.info(f"File saved successfully: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"File save failed: {e}")
        raise


def get_supported_image_extensions() -> List[str]:
    """Get supported image extensions"""
    return [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".gif"]


def is_valid_image_file(filename: str) -> bool:
    """Check if it's a valid image file"""
    if not filename:
        return False
    return Path(filename).suffix.lower() in get_supported_image_extensions()


def cleanup_temp_files(temp_dir: str, max_age_hours: int = 24) -> None:
    """Clean up temporary files"""
    try:
        import time
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        for file_path in Path(temp_dir).glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_seconds:
                    try:
                        file_path.unlink()
                        logger.info(f"Cleaned up temp file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Failed to clean up temp files: {e}")


def get_file_size_mb(file_path: str) -> float:
    """Get file size (MB)"""
    return os.path.getsize(file_path) / (1024 * 1024)

"""
Constants definition
"""

# AI model related constants
AI_MODEL_CONFIG = {
    "yolov11": {
        "model_path": "models/yolov11.pt",
        "confidence_threshold": 0.5,
        "iou_threshold": 0.45,
        "max_det": 300,
        "classes": None,  # Detect all classes
    }
}

# MAVLink related constants
MAVLINK_CONFIG = {
    "default_port": 5760,
    "default_host": "0.0.0.0",
    "timeout": 30,
    "max_message_size": 1024,
}

# Database related constants
DATABASE_CONFIG = {
    "default_timeout": 30,
    "max_pool_size": 10,
    "min_pool_size": 1,
}

# API related constants
API_CONFIG = {
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "allowed_image_types": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
    "max_batch_size": 10,
}

# Logging related constants
LOG_CONFIG = {
    "level": "INFO",
    "format": "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    "rotation": "1 day",
    "retention": "30 days",
}

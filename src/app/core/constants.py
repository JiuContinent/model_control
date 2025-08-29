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

# Real-time AI related constants
REALTIME_AI_CONFIG = {
    "default_device": "cuda",  # Default to GPU if available
    "fallback_device": "cpu",
    "model_variants": {
        "yolov11n": {
            "model_file": "yolov11n.pt",
            "description": "Nano - Fastest, lowest accuracy",
            "default_device": "cuda",
            "recommended_batch_size": 4
        },
        "yolov11s": {
            "model_file": "yolov11s.pt", 
            "description": "Small - Fast, good balance",
            "default_device": "cuda",
            "recommended_batch_size": 3
        },
        "yolov11m": {
            "model_file": "yolov11m.pt",
            "description": "Medium - Moderate speed, better accuracy",
            "default_device": "cuda",
            "recommended_batch_size": 2
        },
        "yolov11l": {
            "model_file": "yolov11l.pt",
            "description": "Large - Slower, high accuracy",
            "default_device": "cuda",
            "recommended_batch_size": 1
        },
        "yolov11x": {
            "model_file": "yolov11x.pt",
            "description": "Extra Large - Slowest, highest accuracy",
            "default_device": "cuda",
            "recommended_batch_size": 1
        }
    },
    "performance_settings": {
        "enable_half_precision": True,  # FP16 for faster GPU inference
        "enable_tensorrt": False,       # TensorRT optimization (requires setup)
        "enable_openvino": False,       # OpenVINO optimization (Intel)
        "warmup_iterations": 3,         # Number of warmup inferences
        "max_workspace_size": "1GB"    # GPU memory limit
    },
    "stream_settings": {
        "default_buffer_size": 1,       # Minimal latency
        "max_retry_attempts": 3,
        "connection_timeout": 30,
        "frame_skip_on_overload": True,
        "adaptive_fps": True
    }
}

# Stream protocol related constants  
STREAM_CONFIG = {
    "rtsp": {
        "default_port": 554,
        "buffer_size": 1,
        "transport": "tcp",  # tcp or udp
        "timeout": 30
    },
    "rtmp": {
        "default_port": 1935, 
        "buffer_size": 1,
        "timeout": 30,
        "backend": "ffmpeg"
    },
    "http": {
        "buffer_size": 3,
        "timeout": 30,
        "user_agent": "ModelControl-AI/1.0"
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

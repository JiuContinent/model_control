
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import asyncio

from app.config import settings
# from app.core.logging import setup_logging
from app.core.exceptions import ModelControlException
from app.api import ai, mavlink, datasource, upload, mqtt, realtime_ai, vehicle_ai, mysql_datasource
from app.mavlink.udp_receiver import start_udp_receiver, stop_udp_receiver
from app.services.mqtt_service import mqtt_service
# from loguru import logger

# Setup logging
# setup_logging()

# Create FastAPI instance
app = FastAPI(
    title="Model Control AI System",
    description="FastAPI-based model control system with YOLOv11 AI recognition",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(ai.router, prefix="/api/v1")
app.include_router(mavlink.router, prefix="/api/v1")
app.include_router(datasource.router, prefix="/api/v1")
app.include_router(upload.router, prefix="/api/v1")
app.include_router(mqtt.router, prefix="/api/v1")
app.include_router(realtime_ai.router, prefix="/api/v1")
app.include_router(vehicle_ai.router, prefix="/api/v1")
app.include_router(mysql_datasource.router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event():
    """Application startup event handler"""
    
    # Log system information including GPU detection
    try:
        from app.realtime_ai.utils.system_utils import log_system_startup_info, validate_environment
        log_system_startup_info()
        
        # Validate environment
        issues = validate_environment()
        if issues:
            print("??  Environment validation warnings:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print("? Environment validation passed")
    except Exception as e:
        print(f"Failed to log system info: {e}")
    
    print("Starting UDP receiver...")
    try:
        await start_udp_receiver()
        print("UDP receiver started successfully, listening on port 14550")
    except Exception as e:
        print(f"Failed to start UDP receiver: {e}")
    
    print("Starting MQTT service...")
    try:
        await mqtt_service.start()
        print("MQTT service started successfully")
    except Exception as e:
        print(f"Failed to start MQTT service: {e}")
    
    # Initialize MySQL multi-source manager
    if settings.USE_MYSQL:
        print("Initializing MySQL multi-source manager...")
        try:
            from app.db.mysql_multi import init_mysql_multi
            await init_mysql_multi()
            print("MySQL multi-source manager initialized successfully")
        except Exception as e:
            print(f"Failed to initialize MySQL multi-source manager: {e}")
    
    print("? Model Control AI System started successfully!")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event handler"""
    print("Stopping UDP receiver...")
    try:
        await stop_udp_receiver()
        print("UDP receiver stopped")
    except Exception as e:
        print(f"Failed to stop UDP receiver: {e}")
    
    print("Stopping MQTT service...")
    try:
        await mqtt_service.stop()
        print("MQTT service stopped")
    except Exception as e:
        print(f"Failed to stop MQTT service: {e}")
    
    # Close MySQL connections
    if settings.USE_MYSQL:
        print("Closing MySQL connections...")
        try:
            from app.db.mysql_multi import mysql_manager
            await mysql_manager.close_all()
            print("MySQL connections closed")
        except Exception as e:
            print(f"Failed to close MySQL connections: {e}")


@app.exception_handler(ModelControlException)
async def model_control_exception_handler(request, exc):
    """Custom exception handler"""
    # logger.error(f"Business exception: {exc}")
    print(f"Business exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": str(exc), "type": exc.__class__.__name__}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    # logger.error(f"Unhandled exception: {exc}")
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


@app.get("/", tags=["Root"])
def read_root():
    """Root path"""
    return {
        "message": "Welcome to Model Control AI System",
        "version": "0.2.0",
        "features": [
            "YOLOv11 AI Object Detection",
            "Real-time AI Stream Recognition",
            "RTSP/RTMP Stream Support",
            "MAVLink Protocol Support",
            "Multi-datasource Management",
            "MySQL Multi-tenant Support",
            "Real-time Data Processing"
        ],
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["Health"])
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "message": "Application is running",
        "version": "0.2.0",
        "services": {
            "ai": "available",
            "mavlink": "available",
            "database": "available"
        }
    }


@app.get("/api/v1/status", tags=["Status"])
def get_system_status():
    """Get system status"""
    return {
        "system": "Model Control AI System",
        "version": "0.2.0",
        "status": "running",
        "endpoints": {
            "ai": "/api/v1/ai",
            "realtime_ai": "/api/v1/realtime-ai",
            "vehicle_ai": "/api/v1/vehicle-ai",
            "mavlink": "/api/v1/mavlink",
            "datasource": "/api/v1/datasource",
            "mysql_datasource": "/api/v1/mysql-datasource",
            "upload": "/api/v1/upload"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=2000,
        reload=True,
        log_level="info"
    )

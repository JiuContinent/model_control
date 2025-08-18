
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.config import settings
# from app.core.logging import setup_logging
from app.core.exceptions import ModelControlException
from app.api import ai, mavlink, datasource, upload, mqtt
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
            "MAVLink Protocol Support",
            "Multi-datasource Management",
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
            "mavlink": "/api/v1/mavlink",
            "datasource": "/api/v1/datasource",
            "upload": "/api/v1/upload"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

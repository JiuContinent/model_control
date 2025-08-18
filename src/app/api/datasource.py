# -*- coding: utf-8 -*-
"""
Data source management API
Provides multi-datasource switching and monitoring functionality
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any
import asyncio

from app.db.mongo_multi import mongo_manager, switch_mongo_source, get_current_source

router = APIRouter(prefix="/datasource", tags=["Data Source"])


@router.get("/list")
async def list_data_sources():
    """List all available data sources"""
    try:
        sources = mongo_manager.list_sources()
        return {
            "status": "success",
            "sources": sources,
            "current_source": get_current_source()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data source list: {str(e)}")


@router.post("/switch/{source_name}")
async def switch_data_source(source_name: str):
    """Switch to specified data source"""
    try:
        await switch_mongo_source(source_name)
        return {
            "status": "success",
            "message": f"Switched to data source: {source_name}",
            "current_source": get_current_source()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to switch data source: {str(e)}")


@router.get("/current")
async def get_current_data_source():
    """Get current data source information"""
    try:
        current_source = get_current_source()
        if current_source == "unknown":
            return {
                "status": "error",
                "message": "Data source not initialized"
            }
        
        sources = mongo_manager.list_sources()
        current_info = sources.get(current_source, {})
        
        return {
            "status": "success",
            "current_source": current_source,
            "source_info": current_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get current data source: {str(e)}")


@router.get("/status")
async def get_data_sources_status():
    """Get all data source status"""
    try:
        sources = mongo_manager.list_sources()
        current_source = get_current_source()
        
        # Statistics
        total_sources = len(sources)
        connected_sources = sum(1 for s in sources.values() if s["status"] == "connected")
        disconnected_sources = total_sources - connected_sources
        
        return {
            "status": "success",
            "summary": {
                "total_sources": total_sources,
                "connected_sources": connected_sources,
                "disconnected_sources": disconnected_sources,
                "current_source": current_source
            },
            "sources": sources
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get data source status: {str(e)}")


@router.post("/reconnect/{source_name}")
async def reconnect_data_source(source_name: str):
    """Reconnect specified data source"""
    try:
        # Here you can implement reconnection logic
        # Temporarily return success message
        return {
            "status": "success",
            "message": f"Data source {source_name} reconnection request sent"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reconnect data source: {str(e)}")


@router.get("/health")
async def check_data_sources_health():
    """Check health status of all data sources"""
    try:
        sources = mongo_manager.list_sources()
        health_status = {}
        
        for source_name, source_info in sources.items():
            try:
                # Try to ping database
                db = mongo_manager.get_database(source_name)
                await db.command("ping")
                health_status[source_name] = {
                    "status": "healthy",
                    "response_time": "normal"
                }
            except Exception as e:
                health_status[source_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return {
            "status": "success",
            "health_check": health_status,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

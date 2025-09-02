"""
MongoDB Multi-Source Manager
Supports dynamic switching between different MongoDB data sources
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from typing import Dict, Optional, List
import asyncio
from contextlib import asynccontextmanager

from app.config import settings


class MongoMultiSourceManager:
    """MongoDB multi-source manager"""
    
    def __init__(self):
        self.clients: Dict[str, AsyncIOMotorClient] = {}
        self.databases: Dict[str, AsyncIOMotorDatabase] = {}
        self.current_source: Optional[str] = None
        self.initialized_models: Dict[str, List] = {}
        
        # Predefined data source configurations
        self.data_sources = {
            "default": {
                "uri": settings.MONGO_URI,
                "db_name": settings.MONGO_DB_NAME,
                "description": "Default data source (control_db)"
            },
            "control": {
                "uri": settings.MONGO_URI,
                "db_name": settings.CONTROL_DB_NAME,
                "description": "Control system data source"
            },
            "dji": {
                "uri": settings.MONGO_URI,
                "db_name": settings.DJI_DB_NAME,
                "description": "DJI equipment data source"
            },
            "ue": {
                "uri": getattr(settings, 'UE_MONGO_URI', settings.MONGO_URI),
                "db_name": getattr(settings, 'UE_MONGO_DB_NAME', 'ue'),
                "description": "UE data source"
            },
            "mavlink": {
                "uri": getattr(settings, 'MAVLINK_MONGO_URI', settings.MONGO_URI),
                "db_name": getattr(settings, 'MAVLINK_MONGO_DB_NAME', settings.MAVLINK_MONGO_DB_NAME),
                "description": "MAVLink dedicated data source"
            },
            "chat": {
                "uri": getattr(settings, 'CHAT_MONGO_URI', settings.MONGO_URI),
                "db_name": getattr(settings, 'CHAT_MONGO_DB_NAME', settings.CHAT_MONGO_DB_NAME),
                "description": "Chat dedicated data source"
            },
            "analytics": {
                "uri": getattr(settings, 'ANALYTICS_MONGO_URI', settings.MONGO_URI),
                "db_name": getattr(settings, 'ANALYTICS_MONGO_DB_NAME', settings.ANALYTICS_MONGO_DB_NAME),
                "description": "Analytics dedicated data source"
            }
        }
    
    async def initialize(self, default_source: str = "default"):
        """Initialize multi-source manager"""
        try:
            print("Initializing multi-source MongoDB connections...")
            
            # Initialize all data sources
            for source_name, config in self.data_sources.items():
                await self._init_source(source_name, config)
            
            # Set default data source
            await self.switch_source(default_source)
            
            print(f"Multi-source MongoDB initialization complete, current source: {self.current_source}")
            
        except Exception as e:
            print(f"Failed to initialize multi-source MongoDB: {e}")
            raise
    
    async def _init_source(self, source_name: str, config: Dict):
        """Initialize single data source"""
        try:
            print(f"Initializing data source: {source_name} -> {config['db_name']}")
            
            # Create client connection
            client = AsyncIOMotorClient(config["uri"])
            
            # Test connection
            await client.admin.command('ping')
            
            # Get database
            db = client[config["db_name"]]
            
            # Store connection
            self.clients[source_name] = client
            self.databases[source_name] = db
            
            print(f"Data source {source_name} initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize data source {source_name}: {e}")
            # If a data source fails, use default configuration
            if source_name != "default":
                print(f"Using default data source configuration for {source_name}")
                await self._init_source(source_name, {
                    "uri": settings.MONGO_URI,
                    "db_name": f"{settings.MONGO_DB_NAME}_{source_name}",
                    "description": f"{source_name} data source (using default config)"
                })
    
    async def switch_source(self, source_name: str):
        """Switch data source"""
        if source_name not in self.databases:
            raise ValueError(f"Data source {source_name} does not exist")
        
        if self.current_source == source_name:
            print(f"Data source is already {source_name}, no need to switch")
            return
        
        print(f"Switching data source: {self.current_source} -> {source_name}")
        
        # Initialize models for new data source
        await self._init_models_for_source(source_name)
        
        self.current_source = source_name
        print(f"Data source switch complete: {source_name}")
    
    async def _init_models_for_source(self, source_name: str):
        """Initialize models for specified data source"""
        if source_name in self.initialized_models:
            return
        
        try:
            db = self.databases[source_name]
            
            # Select different models based on data source type
            if source_name == "mavlink":
                from app.models.mavlink_models import MavlinkMessage, MavlinkSession, MavlinkStatistics
                models = [MavlinkMessage, MavlinkSession, MavlinkStatistics]
            elif source_name == "chat":
                # Chat models can be added here if needed
                models = []
            elif source_name == "analytics":
                # Can add analytics-related models
                models = []
            else:
                # Default data source contains all models
                from app.models.mavlink_models import MavlinkMessage, MavlinkSession, MavlinkStatistics
                models = [MavlinkMessage, MavlinkSession, MavlinkStatistics]
            
            if models:
                await init_beanie(database=db, document_models=models)
                self.initialized_models[source_name] = models
                print(f"Data source {source_name} models initialized, total {len(models)} models")
            
        except Exception as e:
            print(f"Failed to initialize models for data source {source_name}: {e}")
    
    def get_current_database(self) -> AsyncIOMotorDatabase:
        """Get current data source database"""
        if not self.current_source:
            raise RuntimeError("No current data source set")
        return self.databases[self.current_source]
    
    def get_database(self, source_name: str) -> AsyncIOMotorDatabase:
        """Get specified data source database"""
        if source_name not in self.databases:
            raise ValueError(f"Data source {source_name} does not exist")
        return self.databases[source_name]
    
    async def close_all(self):
        """Close all data source connections"""
        print("Closing all MongoDB connections...")
        
        for source_name, client in self.clients.items():
            try:
                client.close()
                print(f"Data source {source_name} connection closed")
            except Exception as e:
                print(f"Error closing data source {source_name} connection: {e}")
        
        self.clients.clear()
        self.databases.clear()
        self.current_source = None
        self.initialized_models.clear()
        
        print("All MongoDB connections closed")
    
    def list_sources(self) -> Dict[str, Dict]:
        """List all available data sources"""
        return {
            name: {
                "uri": config["uri"],
                "db_name": config["db_name"],
                "description": config["description"],
                "status": "connected" if name in self.databases else "disconnected",
                "current": name == self.current_source
            }
            for name, config in self.data_sources.items()
        }
    
    @asynccontextmanager
    async def use_source(self, source_name: str):
        """Context manager for temporarily using specified data source"""
        original_source = self.current_source
        try:
            await self.switch_source(source_name)
            yield self.get_current_database()
        finally:
            if original_source:
                await self.switch_source(original_source)


# Global multi-source manager instance
mongo_manager = MongoMultiSourceManager()


async def init_mongo_multi():
    """Initialize multi-source MongoDB"""
    await mongo_manager.initialize()


async def get_mongo_db(source_name: str = None) -> AsyncIOMotorDatabase:
    """Get MongoDB database instance"""
    if source_name:
        return mongo_manager.get_database(source_name)
    return mongo_manager.get_current_database()


async def switch_mongo_source(source_name: str):
    """Switch MongoDB data source"""
    await mongo_manager.switch_source(source_name)


def get_current_source() -> str:
    """Get current data source name"""
    return mongo_manager.current_source or "unknown"

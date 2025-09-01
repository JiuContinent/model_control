"""
MySQL Multi-Source Manager
支持动态切换不同的MySQL数据源，包括多租户数据库和ruoyi_vue_pro
"""
import aiomysql
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import MetaData
from typing import Dict, Optional, AsyncGenerator
import asyncio
from contextlib import asynccontextmanager

from app.config import settings

# SQLAlchemy基础模型
Base = declarative_base()


class MySQLMultiSourceManager:
    """MySQL多数据源管理器"""
    
    def __init__(self):
        self.engines: Dict[str, any] = {}
        self.session_makers: Dict[str, async_sessionmaker] = {}
        self.current_source: Optional[str] = None
        self.metadata = MetaData()
        
        # 动态构建数据源配置，只包含已配置的数据源
        self.data_sources = {}
        
        # 检查并添加tenant_2数据源
        if hasattr(settings, 'MYSQL_TENANT_2_DB') and settings.MYSQL_TENANT_2_DB:
            self.data_sources["tenant_2"] = {
                "database": settings.MYSQL_TENANT_2_DB,
                "description": "租户2数据库"
            }
        
        # 检查并添加tenant_3数据源
        if hasattr(settings, 'MYSQL_TENANT_3_DB') and settings.MYSQL_TENANT_3_DB:
            self.data_sources["tenant_3"] = {
                "database": settings.MYSQL_TENANT_3_DB,
                "description": "租户3数据库"
            }
        
        # 检查并添加ruoyi_vue_pro数据源
        if hasattr(settings, 'MYSQL_RUOYI_VUE_PRO_DB') and settings.MYSQL_RUOYI_VUE_PRO_DB:
            self.data_sources["ruoyi_vue_pro"] = {
                "database": settings.MYSQL_RUOYI_VUE_PRO_DB,
                "description": "若依Vue Pro数据库"
            }
        
        # 如果没有配置任何数据源，则报错
        if not self.data_sources:
            raise ValueError("未配置任何MySQL数据源，请在配置文件中设置至少一个 MYSQL_*_DB 配置项")
    
    def _build_connection_url(self, database: str) -> str:
        """构建数据库连接URL"""
        return (
            f"mysql+aiomysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}@"
            f"{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{database}"
            f"?charset={settings.MYSQL_CHARSET}"
        )
    
    async def initialize(self, default_source: str = None):
        """初始化多数据源管理器"""
        try:
            print("正在初始化MySQL多数据源连接...")
            
            # 初始化所有数据源
            for source_name, config in self.data_sources.items():
                await self._init_source(source_name, config)
            
            # 设置默认数据源
            default_db = default_source or settings.MYSQL_DEFAULT_DB
            if default_db in self.data_sources:
                await self.switch_source(default_db)
            else:
                # 如果默认数据库不在配置中，使用第一个可用的
                available_sources = list(self.engines.keys())
                if available_sources:
                    await self.switch_source(available_sources[0])
            
            print(f"MySQL多数据源初始化完成，当前数据源: {self.current_source}")
            
        except Exception as e:
            print(f"MySQL多数据源初始化失败: {e}")
            raise
    
    async def _init_source(self, source_name: str, config: Dict):
        """初始化单个数据源"""
        try:
            print(f"正在初始化数据源: {source_name} -> {config['database']}")
            
            # 构建连接URL
            connection_url = self._build_connection_url(config["database"])
            
            # 创建异步引擎
            engine = create_async_engine(
                connection_url,
                echo=False,  # 设为True可以看到SQL日志
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 测试连接
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            
            # 创建session maker
            session_maker = async_sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # 存储连接
            self.engines[source_name] = engine
            self.session_makers[source_name] = session_maker
            
            print(f"数据源 {source_name} 初始化成功")
            
        except Exception as e:
            print(f"数据源 {source_name} 初始化失败: {e}")
            # 不抛出异常，允许其他数据源继续初始化
    
    async def switch_source(self, source_name: str):
        """切换数据源"""
        if source_name not in self.engines:
            raise ValueError(f"数据源 {source_name} 不存在或未初始化")
        
        if self.current_source == source_name:
            print(f"数据源已经是 {source_name}，无需切换")
            return
        
        print(f"切换数据源: {self.current_source} -> {source_name}")
        self.current_source = source_name
        print(f"数据源切换完成: {source_name}")
    
    async def get_session(self, source_name: str = None) -> AsyncSession:
        """获取数据库会话"""
        target_source = source_name or self.current_source
        
        if not target_source:
            raise RuntimeError("没有设置当前数据源")
            
        if target_source not in self.session_makers:
            raise ValueError(f"数据源 {target_source} 不存在或未初始化")
        
        session_maker = self.session_makers[target_source]
        return session_maker()
    
    @asynccontextmanager
    async def get_db_session(self, source_name: str = None) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话的上下文管理器"""
        session = await self.get_session(source_name)
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    def get_current_engine(self):
        """获取当前数据源的引擎"""
        if not self.current_source:
            raise RuntimeError("没有设置当前数据源")
        return self.engines[self.current_source]
    
    def get_engine(self, source_name: str):
        """获取指定数据源的引擎"""
        if source_name not in self.engines:
            raise ValueError(f"数据源 {source_name} 不存在")
        return self.engines[source_name]
    
    async def close_all(self):
        """关闭所有数据源连接"""
        print("正在关闭所有MySQL连接...")
        
        for source_name, engine in self.engines.items():
            try:
                await engine.dispose()
                print(f"数据源 {source_name} 连接已关闭")
            except Exception as e:
                print(f"关闭数据源 {source_name} 连接时出错: {e}")
        
        self.engines.clear()
        self.session_makers.clear()
        self.current_source = None
        
        print("所有MySQL连接已关闭")
    
    def list_sources(self) -> Dict[str, Dict]:
        """列出所有可用数据源"""
        return {
            name: {
                "database": config["database"],
                "description": config["description"],
                "status": "connected" if name in self.engines else "disconnected",
                "current": name == self.current_source
            }
            for name, config in self.data_sources.items()
        }
    
    @asynccontextmanager
    async def use_source(self, source_name: str):
        """临时使用指定数据源的上下文管理器"""
        original_source = self.current_source
        try:
            await self.switch_source(source_name)
            async with self.get_db_session() as session:
                yield session
        finally:
            if original_source:
                await self.switch_source(original_source)
    
    async def execute_raw_sql(self, sql: str, params: tuple = None, source_name: str = None):
        """执行原生SQL查询"""
        target_source = source_name or self.current_source
        if not target_source:
            raise RuntimeError("没有设置当前数据源")
        
        engine = self.engines[target_source]
        async with engine.begin() as conn:
            if params:
                result = await conn.execute(sql, params)
            else:
                result = await conn.execute(sql)
            return result.fetchall() if result.returns_rows else result.rowcount
    
    async def test_connection(self, source_name: str = None) -> bool:
        """测试数据库连接"""
        try:
            target_source = source_name or self.current_source
            if not target_source:
                return False
            
            engine = self.engines.get(target_source)
            if not engine:
                return False
            
            async with engine.begin() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            print(f"数据源 {target_source} 连接测试失败: {e}")
            return False


# 全局MySQL多数据源管理器实例
mysql_manager = MySQLMultiSourceManager()


async def init_mysql_multi():
    """初始化MySQL多数据源"""
    if settings.USE_MYSQL:
        await mysql_manager.initialize()


async def get_mysql_session(source_name: str = None) -> AsyncSession:
    """获取MySQL数据库会话"""
    return await mysql_manager.get_session(source_name)


async def switch_mysql_source(source_name: str):
    """切换MySQL数据源"""
    await mysql_manager.switch_source(source_name)


def get_current_mysql_source() -> str:
    """获取当前MySQL数据源名称"""
    return mysql_manager.current_source or "unknown"


@asynccontextmanager
async def get_mysql_db(source_name: str = None) -> AsyncGenerator[AsyncSession, None]:
    """获取MySQL数据库会话的上下文管理器"""
    async with mysql_manager.get_db_session(source_name) as session:
        yield session

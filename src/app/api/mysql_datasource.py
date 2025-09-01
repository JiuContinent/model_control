"""
MySQL数据源管理API
提供MySQL多数据源切换和管理功能
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from sqlalchemy import text
from datetime import datetime

from app.db.mysql_multi import mysql_manager, get_mysql_db, switch_mysql_source, get_current_mysql_source
from app.models.mysql_models import Base, ALL_MODELS

router = APIRouter(prefix="/mysql-datasource", tags=["MySQL数据源管理"])


class DataSourceInfo(BaseModel):
    """数据源信息响应模型"""
    name: str
    database: str
    description: str
    status: str
    current: bool


class SwitchDataSourceRequest(BaseModel):
    """切换数据源请求模型"""
    source_name: str


class CreateTablesRequest(BaseModel):
    """创建表请求模型"""
    source_name: Optional[str] = None
    table_type: str = "tenant"  # tenant 或 ruoyi


class QueryRequest(BaseModel):
    """SQL查询请求模型"""
    sql: str
    source_name: Optional[str] = None


@router.get("/sources", response_model=Dict[str, DataSourceInfo])
async def list_data_sources():
    """列出所有可用的MySQL数据源"""
    try:
        sources = mysql_manager.list_sources()
        return {
            name: DataSourceInfo(
                name=name,
                database=info["database"],
                description=info["description"],
                status=info["status"],
                current=info["current"]
            )
            for name, info in sources.items()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据源列表失败: {str(e)}")


@router.get("/current")
async def get_current_data_source():
    """获取当前数据源信息"""
    try:
        current_source = get_current_mysql_source()
        if current_source == "unknown":
            raise HTTPException(status_code=404, detail="没有设置当前数据源")
        
        sources = mysql_manager.list_sources()
        if current_source not in sources:
            raise HTTPException(status_code=404, detail=f"当前数据源 {current_source} 不存在")
        
        source_info = sources[current_source]
        return {
            "current_source": current_source,
            "database": source_info["database"],
            "description": source_info["description"],
            "status": source_info["status"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取当前数据源失败: {str(e)}")


@router.post("/switch")
async def switch_data_source(request: SwitchDataSourceRequest):
    """切换数据源"""
    try:
        await switch_mysql_source(request.source_name)
        return {
            "success": True,
            "message": f"成功切换到数据源: {request.source_name}",
            "current_source": request.source_name
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换数据源失败: {str(e)}")


@router.post("/test-connection")
async def test_connection(source_name: Optional[str] = None):
    """测试数据库连接"""
    try:
        target_source = source_name or get_current_mysql_source()
        is_connected = await mysql_manager.test_connection(target_source)
        
        return {
            "source_name": target_source,
            "connected": is_connected,
            "message": "连接正常" if is_connected else "连接失败",
            "test_time": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试连接失败: {str(e)}")


@router.post("/create-tables")
async def create_tables(request: CreateTablesRequest):
    """在指定数据源中创建表"""
    try:
        target_source = request.source_name or get_current_mysql_source()
        
        if target_source == "unknown":
            raise HTTPException(status_code=400, detail="没有指定数据源")
        
        # 获取对应的模型
        if request.table_type not in ALL_MODELS:
            raise HTTPException(status_code=400, detail=f"不支持的表类型: {request.table_type}")
        
        models = ALL_MODELS[request.table_type]
        engine = mysql_manager.get_engine(target_source)
        
        # 创建表
        async with engine.begin() as conn:
            for model in models:
                await conn.run_sync(model.metadata.create_all)
        
        return {
            "success": True,
            "message": f"在数据源 {target_source} 中成功创建 {request.table_type} 类型的表",
            "source_name": target_source,
            "table_type": request.table_type,
            "tables_created": len(models)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建表失败: {str(e)}")


@router.post("/execute-sql")
async def execute_sql(request: QueryRequest):
    """执行原生SQL查询"""
    try:
        target_source = request.source_name or get_current_mysql_source()
        
        if target_source == "unknown":
            raise HTTPException(status_code=400, detail="没有指定数据源")
        
        # 安全检查：禁止危险操作
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        sql_upper = request.sql.upper().strip()
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise HTTPException(status_code=403, detail=f"禁止执行包含 {keyword} 的SQL语句")
        
        # 执行SQL
        result = await mysql_manager.execute_raw_sql(request.sql, source_name=target_source)
        
        return {
            "success": True,
            "source_name": target_source,
            "sql": request.sql,
            "result": result if isinstance(result, list) else f"影响行数: {result}",
            "execution_time": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行SQL失败: {str(e)}")


@router.get("/tables")
async def list_tables(source_name: Optional[str] = None):
    """列出数据源中的所有表"""
    try:
        target_source = source_name or get_current_mysql_source()
        
        if target_source == "unknown":
            raise HTTPException(status_code=400, detail="没有指定数据源")
        
        # 查询表信息
        sql = """
        SELECT 
            TABLE_NAME as table_name,
            TABLE_COMMENT as table_comment,
            TABLE_ROWS as table_rows,
            CREATE_TIME as create_time
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
        ORDER BY TABLE_NAME
        """
        
        result = await mysql_manager.execute_raw_sql(sql, source_name=target_source)
        
        tables = []
        for row in result:
            tables.append({
                "table_name": row[0],
                "table_comment": row[1] or "",
                "table_rows": row[2] or 0,
                "create_time": row[3].isoformat() if row[3] else None
            })
        
        return {
            "source_name": target_source,
            "database": mysql_manager.data_sources[target_source]["database"],
            "table_count": len(tables),
            "tables": tables
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表列表失败: {str(e)}")


@router.get("/table/{table_name}/structure")
async def get_table_structure(table_name: str, source_name: Optional[str] = None):
    """获取表结构信息"""
    try:
        target_source = source_name or get_current_mysql_source()
        
        if target_source == "unknown":
            raise HTTPException(status_code=400, detail="没有指定数据源")
        
        # 查询表结构
        sql = """
        SELECT 
            COLUMN_NAME as column_name,
            DATA_TYPE as data_type,
            IS_NULLABLE as is_nullable,
            COLUMN_DEFAULT as column_default,
            COLUMN_COMMENT as column_comment,
            COLUMN_KEY as column_key,
            EXTRA as extra
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        
        result = await mysql_manager.execute_raw_sql(sql, (table_name,), source_name=target_source)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"表 {table_name} 不存在")
        
        columns = []
        for row in result:
            columns.append({
                "column_name": row[0],
                "data_type": row[1],
                "is_nullable": row[2] == "YES",
                "column_default": row[3],
                "column_comment": row[4] or "",
                "column_key": row[5] or "",
                "extra": row[6] or ""
            })
        
        return {
            "source_name": target_source,
            "table_name": table_name,
            "column_count": len(columns),
            "columns": columns
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表结构失败: {str(e)}")


@router.get("/health")
async def health_check():
    """MySQL数据源健康检查"""
    try:
        sources = mysql_manager.list_sources()
        health_status = {}
        
        for name, info in sources.items():
            is_connected = await mysql_manager.test_connection(name)
            health_status[name] = {
                "database": info["database"],
                "status": "healthy" if is_connected else "unhealthy",
                "connected": is_connected
            }
        
        current_source = get_current_mysql_source()
        overall_status = "healthy" if current_source != "unknown" and health_status.get(current_source, {}).get("connected", False) else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "current_source": current_source,
            "sources": health_status,
            "check_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "check_time": datetime.now().isoformat()
        }

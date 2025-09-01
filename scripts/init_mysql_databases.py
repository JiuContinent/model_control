#!/usr/bin/env python3
"""
MySQL数据库初始化脚本
用于创建多租户数据库和初始化表结构
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.config import settings
from app.db.mysql_multi import mysql_manager
from app.models.mysql_models import Base, ALL_MODELS


async def create_databases():
    """创建所有租户数据库"""
    import aiomysql
    
    print("正在连接MySQL服务器...")
    
    # 连接到MySQL服务器（不指定数据库）
    connection = await aiomysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        charset=settings.MYSQL_CHARSET
    )
    
    try:
        async with connection.cursor() as cursor:
            # 动态收集需要创建的数据库
            databases = []
            
            if hasattr(settings, 'MYSQL_TENANT_2_DB') and settings.MYSQL_TENANT_2_DB:
                databases.append(settings.MYSQL_TENANT_2_DB)
            
            if hasattr(settings, 'MYSQL_TENANT_3_DB') and settings.MYSQL_TENANT_3_DB:
                databases.append(settings.MYSQL_TENANT_3_DB)
                
            if hasattr(settings, 'MYSQL_RUOYI_VUE_PRO_DB') and settings.MYSQL_RUOYI_VUE_PRO_DB:
                databases.append(settings.MYSQL_RUOYI_VUE_PRO_DB)
            
            if not databases:
                print("警告: 没有配置任何数据库，跳过数据库创建")
                return
            
            for db_name in databases:
                print(f"创建数据库: {db_name}")
                await cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"数据库 {db_name} 创建成功")
            
            await connection.commit()
            print("所有数据库创建完成")
            
    finally:
        connection.close()


async def initialize_tables():
    """初始化所有数据库的表结构"""
    print("正在初始化MySQL多数据源管理器...")
    await mysql_manager.initialize()
    
    # 动态构建数据源映射，只包含已配置的数据源
    data_source_mappings = {}
    
    if "tenant_2" in mysql_manager.data_sources:
        data_source_mappings["tenant_2"] = "tenant"
    
    if "tenant_3" in mysql_manager.data_sources:
        data_source_mappings["tenant_3"] = "tenant"
        
    if "ruoyi_vue_pro" in mysql_manager.data_sources:
        data_source_mappings["ruoyi_vue_pro"] = "ruoyi"
    
    if not data_source_mappings:
        print("警告: 没有可用的数据源，跳过表创建")
        await mysql_manager.close_all()
        return
    
    for source_name, table_type in data_source_mappings.items():
        print(f"正在为数据源 {source_name} 创建 {table_type} 类型的表...")
        
        try:
            models = ALL_MODELS[table_type]
            engine = mysql_manager.get_engine(source_name)
            
            # 创建表
            async with engine.begin() as conn:
                # 为每个模型单独创建表，以便更好的错误处理
                for model in models:
                    try:
                        await conn.run_sync(model.metadata.create_all)
                        print(f"  - 表 {model.__tablename__} 创建成功")
                    except Exception as e:
                        print(f"  - 表 {model.__tablename__} 创建失败: {e}")
            
            print(f"数据源 {source_name} 的表创建完成")
            
        except Exception as e:
            print(f"数据源 {source_name} 初始化失败: {e}")
    
    await mysql_manager.close_all()


async def insert_sample_data():
    """插入示例数据"""
    print("正在插入示例数据...")
    await mysql_manager.initialize()
    
    # 切换到tenant_2数据源并插入示例数据
    await mysql_manager.switch_source("tenant_2")
    
    async with mysql_manager.get_db_session() as session:
        from app.models.mysql_models import TenantUser, TenantRole
        
        # 创建示例用户
        sample_user = TenantUser(
            username="admin",
            email="admin@tenant2.com",
            nickname="管理员",
            tenant_id=2
        )
        session.add(sample_user)
        
        # 创建示例角色
        sample_role = TenantRole(
            name="管理员",
            code="admin",
            description="系统管理员角色",
            tenant_id=2
        )
        session.add(sample_role)
        
        await session.commit()
        print("租户2示例数据插入成功")
    
    # 切换到ruoyi_vue_pro数据源并插入示例数据
    await mysql_manager.switch_source("ruoyi_vue_pro")
    
    async with mysql_manager.get_db_session() as session:
        from app.models.mysql_models import RuoyiUser, RuoyiRole
        
        # 创建示例用户
        sample_user = RuoyiUser(
            username="admin",
            nickname="超级管理员",
            email="admin@ruoyi.com",
            status=0
        )
        session.add(sample_user)
        
        # 创建示例角色
        sample_role = RuoyiRole(
            role_name="超级管理员",
            role_key="admin",
            role_sort=1,
            status=0
        )
        session.add(sample_role)
        
        await session.commit()
        print("若依Vue Pro示例数据插入成功")
    
    await mysql_manager.close_all()


async def main():
    """主函数"""
    print("=" * 60)
    print("MySQL多租户数据库初始化脚本")
    print("=" * 60)
    
    try:
        # 步骤1: 创建数据库
        print("\n步骤1: 创建数据库")
        await create_databases()
        
        # 步骤2: 初始化表结构
        print("\n步骤2: 初始化表结构")
        await initialize_tables()
        
        # 步骤3: 插入示例数据
        print("\n步骤3: 插入示例数据")
        await insert_sample_data()
        
        print("\n" + "=" * 60)
        print("MySQL多租户数据库初始化完成！")
        print("=" * 60)
        
        print("\n可用的数据源:")
        print(f"- tenant_2: {settings.MYSQL_TENANT_2_DB}")
        print(f"- tenant_3: {settings.MYSQL_TENANT_3_DB}")
        print(f"- ruoyi_vue_pro: {settings.MYSQL_RUOYI_VUE_PRO_DB}")
        
        print(f"\n默认数据源: {settings.MYSQL_DEFAULT_DB}")
        print("启动服务器后可通过 /api/v1/mysql-datasource 接口管理数据源")
        
    except Exception as e:
        print(f"\n初始化过程中发生错误: {e}")
        print("请检查MySQL配置和连接信息")
        return 1
    
    return 0


if __name__ == "__main__":
    # 检查配置
    if not settings.USE_MYSQL:
        print("错误: MySQL未启用，请在配置中设置 USE_MYSQL=true")
        sys.exit(1)
    
    if not settings.MYSQL_PASSWORD:
        print("警告: MySQL密码为空，请确保MySQL配置正确")
    
    # 运行初始化
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

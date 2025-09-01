#!/usr/bin/env python3
"""
MySQL多数据源使用示例
展示如何在应用中使用MySQL多数据源功能
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.db.mysql_multi import get_mysql_db, switch_mysql_source, mysql_manager
from app.models.mysql_models import TenantUser, TenantRole, RuoyiUser, RuoyiRole


async def example_basic_usage():
    """基本使用示例"""
    print("=" * 50)
    print("基本使用示例")
    print("=" * 50)
    
    # 初始化
    await mysql_manager.initialize()
    
    # 1. 切换到tenant_2数据源
    print("1. 切换到tenant_2数据源")
    await switch_mysql_source("tenant_2")
    
    async with get_mysql_db() as session:
        # 查询用户
        result = await session.execute("SELECT COUNT(*) FROM tenant_users")
        count = result.scalar()
        print(f"   tenant_2中的用户数量: {count}")
    
    # 2. 切换到ruoyi_vue_pro数据源
    print("2. 切换到ruoyi_vue_pro数据源")
    await switch_mysql_source("ruoyi_vue_pro")
    
    async with get_mysql_db() as session:
        # 查询用户
        result = await session.execute("SELECT COUNT(*) FROM ruoyi_users")
        count = result.scalar()
        print(f"   ruoyi_vue_pro中的用户数量: {count}")


async def example_data_operations():
    """数据操作示例"""
    print("\n" + "=" * 50)
    print("数据操作示例")
    print("=" * 50)
    
    # 在tenant_2中创建用户
    print("1. 在tenant_2中创建用户")
    await switch_mysql_source("tenant_2")
    
    async with get_mysql_db() as session:
        # 创建新用户
        new_user = TenantUser(
            username=f"test_user_{datetime.now().strftime('%H%M%S')}",
            email=f"test_{datetime.now().strftime('%H%M%S')}@example.com",
            nickname="测试用户",
            tenant_id=2
        )
        session.add(new_user)
        await session.commit()
        
        print(f"   创建用户: {new_user.username}")
        
        # 查询刚创建的用户
        result = await session.execute(
            "SELECT username, email FROM tenant_users WHERE username = :username",
            {"username": new_user.username}
        )
        user_data = result.fetchone()
        if user_data:
            print(f"   查询结果: {user_data[0]} - {user_data[1]}")
    
    # 在ruoyi_vue_pro中创建用户
    print("2. 在ruoyi_vue_pro中创建用户")
    await switch_mysql_source("ruoyi_vue_pro")
    
    async with get_mysql_db() as session:
        # 创建新用户
        new_user = RuoyiUser(
            username=f"ruoyi_user_{datetime.now().strftime('%H%M%S')}",
            nickname="若依测试用户",
            email=f"ruoyi_{datetime.now().strftime('%H%M%S')}@example.com"
        )
        session.add(new_user)
        await session.commit()
        
        print(f"   创建用户: {new_user.username}")


async def example_multi_source_operations():
    """多数据源操作示例"""
    print("\n" + "=" * 50)
    print("多数据源操作示例")
    print("=" * 50)
    
    # 使用临时数据源切换
    print("1. 使用临时数据源切换")
    
    # 设置默认数据源为tenant_2
    await switch_mysql_source("tenant_2")
    print(f"   当前数据源: {mysql_manager.current_source}")
    
    # 临时切换到tenant_3
    async with mysql_manager.use_source("tenant_3") as session:
        print(f"   临时切换到: tenant_3")
        result = await session.execute("SELECT DATABASE() as db_name")
        db_name = result.scalar()
        print(f"   当前数据库: {db_name}")
        
        # 在tenant_3中创建角色
        new_role = TenantRole(
            name="临时角色",
            code="temp_role",
            description="这是在tenant_3中创建的临时角色",
            tenant_id=3
        )
        session.add(new_role)
        # 注意: 在上下文管理器中会自动提交
    
    # 确认已切换回原数据源
    print(f"   切换回数据源: {mysql_manager.current_source}")
    
    # 2. 同时查询多个数据源
    print("2. 同时查询多个数据源")
    
    sources_data = {}
    for source_name in ["tenant_2", "tenant_3", "ruoyi_vue_pro"]:
        try:
            await switch_mysql_source(source_name)
            async with get_mysql_db() as session:
                result = await session.execute("SELECT DATABASE() as db_name")
                db_name = result.scalar()
                
                # 根据数据源类型查询不同的表
                if source_name in ["tenant_2", "tenant_3"]:
                    result = await session.execute("SELECT COUNT(*) FROM tenant_users")
                    count = result.scalar()
                    table_name = "tenant_users"
                else:
                    result = await session.execute("SELECT COUNT(*) FROM ruoyi_users")
                    count = result.scalar()
                    table_name = "ruoyi_users"
                
                sources_data[source_name] = {
                    "database": db_name,
                    "table": table_name,
                    "count": count
                }
        except Exception as e:
            sources_data[source_name] = {"error": str(e)}
    
    for source, data in sources_data.items():
        if "error" in data:
            print(f"   {source}: 查询失败 - {data['error']}")
        else:
            print(f"   {source}: 数据库={data['database']}, 表={data['table']}, 记录数={data['count']}")


async def example_transaction_handling():
    """事务处理示例"""
    print("\n" + "=" * 50)
    print("事务处理示例")
    print("=" * 50)
    
    await switch_mysql_source("tenant_2")
    
    # 成功的事务
    print("1. 成功的事务")
    async with get_mysql_db() as session:
        user = TenantUser(
            username=f"tx_user_{datetime.now().strftime('%H%M%S')}",
            nickname="事务测试用户",
            tenant_id=2
        )
        session.add(user)
        
        role = TenantRole(
            name="事务测试角色",
            code="tx_role",
            tenant_id=2
        )
        session.add(role)
        
        # 事务会自动提交
        print("   用户和角色创建成功（事务已提交）")
    
    # 失败的事务（模拟）
    print("2. 失败的事务（模拟）")
    try:
        async with get_mysql_db() as session:
            user = TenantUser(
                username=f"fail_user_{datetime.now().strftime('%H%M%S')}",
                nickname="会失败的用户",
                tenant_id=2
            )
            session.add(user)
            
            # 模拟错误
            raise ValueError("模拟的业务错误")
            
    except ValueError as e:
        print(f"   事务失败并回滚: {e}")


async def main():
    """主函数"""
    try:
        await example_basic_usage()
        await example_data_operations()
        await example_multi_source_operations()
        await example_transaction_handling()
        
        print("\n" + "=" * 50)
        print("✅ 所有示例执行完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 示例执行过程中发生错误: {e}")
    finally:
        # 关闭所有连接
        await mysql_manager.close_all()


if __name__ == "__main__":
    print("MySQL多数据源使用示例")
    print("请确保已运行数据库初始化脚本: python scripts/init_mysql_databases.py")
    print()
    
    asyncio.run(main())

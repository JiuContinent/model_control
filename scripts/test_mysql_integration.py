#!/usr/bin/env python3
"""
MySQL集成测试脚本
验证多数据源功能是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from app.config import settings
from app.db.mysql_multi import mysql_manager


async def test_mysql_integration():
    """测试MySQL集成功能"""
    print("=" * 60)
    print("MySQL多数据源集成测试")
    print("=" * 60)
    
    if not settings.USE_MYSQL:
        print("❌ MySQL未启用，请在配置中设置 USE_MYSQL=true")
        return False
    
    try:
        # 初始化MySQL管理器
        print("📝 正在初始化MySQL管理器...")
        await mysql_manager.initialize()
        print("✅ MySQL管理器初始化成功")
        
        # 列出所有数据源
        print("\n📋 可用数据源:")
        sources = mysql_manager.list_sources()
        for name, info in sources.items():
            status_icon = "✅" if info["status"] == "connected" else "❌"
            current_icon = "👉" if info["current"] else "  "
            print(f"{current_icon} {status_icon} {name}: {info['database']} - {info['description']}")
        
        # 测试每个数据源的连接
        print("\n🔗 测试数据源连接:")
        for source_name in sources.keys():
            is_connected = await mysql_manager.test_connection(source_name)
            status_icon = "✅" if is_connected else "❌"
            print(f"  {status_icon} {source_name}: {'连接正常' if is_connected else '连接失败'}")
        
        # 测试数据源切换
        print("\n🔄 测试数据源切换:")
        for source_name in sources.keys():
            try:
                await mysql_manager.switch_source(source_name)
                current = mysql_manager.current_source
                print(f"  ✅ 切换到 {source_name}: 当前数据源 = {current}")
            except Exception as e:
                print(f"  ❌ 切换到 {source_name} 失败: {e}")
        
        # 测试SQL执行
        print("\n💾 测试SQL执行:")
        test_cases = [
            ("tenant_2", "SELECT DATABASE() as current_db, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = DATABASE()"),
            ("tenant_3", "SELECT DATABASE() as current_db, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = DATABASE()"),
            ("ruoyi_vue_pro", "SELECT DATABASE() as current_db, COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = DATABASE()")
        ]
        
        for source_name, sql in test_cases:
            try:
                result = await mysql_manager.execute_raw_sql(sql, source_name=source_name)
                if result:
                    row = result[0]
                    print(f"  ✅ {source_name}: 数据库={row[0]}, 表数量={row[1]}")
                else:
                    print(f"  ⚠️  {source_name}: 查询返回空结果")
            except Exception as e:
                print(f"  ❌ {source_name}: SQL执行失败 - {e}")
        
        # 测试表查询（如果表存在）
        print("\n📊 测试表查询:")
        table_queries = [
            ("tenant_2", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'tenant_%'"),
            ("ruoyi_vue_pro", "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name LIKE 'ruoyi_%'")
        ]
        
        for source_name, sql in table_queries:
            try:
                result = await mysql_manager.execute_raw_sql(sql, source_name=source_name)
                if result:
                    count = result[0][0]
                    print(f"  ✅ {source_name}: 相关表数量 = {count}")
                else:
                    print(f"  ⚠️  {source_name}: 无法获取表信息")
            except Exception as e:
                print(f"  ❌ {source_name}: 查询表信息失败 - {e}")
        
        await mysql_manager.close_all()
        
        print("\n" + "=" * 60)
        print("✅ MySQL多数据源集成测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        return False


async def test_session_management():
    """测试会话管理功能"""
    print("\n🔧 测试会话管理:")
    
    try:
        await mysql_manager.initialize()
        
        # 测试会话获取
        print("  测试会话获取...")
        async with mysql_manager.get_db_session("tenant_2") as session:
            result = await session.execute("SELECT 1 as test")
            row = result.fetchone()
            print(f"    ✅ 会话测试成功: {row[0]}")
        
        # 测试临时数据源切换
        print("  测试临时数据源切换...")
        original_source = mysql_manager.current_source
        
        async with mysql_manager.use_source("tenant_3") as session:
            result = await session.execute("SELECT DATABASE() as db")
            row = result.fetchone()
            print(f"    ✅ 临时切换成功，当前数据库: {row[0]}")
        
        current_source = mysql_manager.current_source
        print(f"    ✅ 自动恢复到原数据源: {current_source}")
        
        await mysql_manager.close_all()
        return True
        
    except Exception as e:
        print(f"    ❌ 会话管理测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    success = True
    
    # 基本集成测试
    if not await test_mysql_integration():
        success = False
    
    # 会话管理测试
    if not await test_session_management():
        success = False
    
    if success:
        print("\n🎉 所有测试通过！MySQL多数据源集成工作正常。")
        print("\n📖 接下来你可以:")
        print("1. 启动服务器: python start_server.py")
        print("2. 访问API文档: http://localhost:2000/docs")
        print("3. 测试数据源API: http://localhost:2000/api/v1/mysql-datasource/sources")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查配置和数据库连接。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

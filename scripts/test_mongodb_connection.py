#!/usr/bin/env python3
"""
MongoDB连接测试脚本
用于验证MongoDB配置是否正确
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    import pymongo
except ImportError:
    print("❌ 错误: 缺少MongoDB相关依赖")
    print("请安装: pip install pymongo motor")
    sys.exit(1)

from app.config import settings


async def test_mongodb_connection():
    """测试MongoDB连接"""
    print("=" * 60)
    print("MongoDB连接测试")
    print("=" * 60)
    
    if not settings.USE_MONGO:
        print("⚠️  MongoDB未启用，请在配置中设置 USE_MONGO=true")
        return False
    
    print(f"📋 配置信息:")
    print(f"   主机: {settings.MONGO_HOST}")
    print(f"   端口: {settings.MONGO_PORT}")
    print(f"   用户名: {settings.MONGO_USERNAME or '(无认证)'}")
    print(f"   认证数据库: {settings.MONGO_AUTH_DB}")
    print(f"   连接URI: {settings.MONGO_URI}")
    print()
    
    try:
        print("🔗 正在测试MongoDB连接...")
        
        # 创建客户端连接
        client = AsyncIOMotorClient(settings.MONGO_URI)
        
        # 测试连接
        await client.admin.command('ping')
        print("✅ MongoDB连接成功!")
        
        # 获取服务器信息
        server_info = await client.admin.command('buildInfo')
        print(f"📊 服务器信息:")
        print(f"   MongoDB版本: {server_info.get('version', 'unknown')}")
        print(f"   平台: {server_info.get('targetArch', 'unknown')}")
        
        # 列出数据库
        print(f"\n📚 可用数据库:")
        databases = await client.list_database_names()
        for db_name in databases:
            print(f"   - {db_name}")
        
        # 测试各个配置的数据库
        test_databases = [
            settings.MONGO_DB_NAME,
            settings.MAVLINK_MONGO_DB_NAME,
            settings.CHAT_MONGO_DB_NAME,
            settings.ANALYTICS_MONGO_DB_NAME
        ]
        
        print(f"\n🔍 测试配置的数据库:")
        for db_name in test_databases:
            try:
                db = client[db_name]
                # 尝试获取集合列表
                collections = await db.list_collection_names()
                print(f"   ✅ {db_name}: {len(collections)} 个集合")
            except Exception as e:
                print(f"   ❌ {db_name}: 访问失败 - {e}")
        
        # 测试写入权限
        print(f"\n✏️  测试写入权限:")
        try:
            test_db = client[settings.MONGO_DB_NAME]
            test_collection = test_db["connection_test"]
            
            # 插入测试文档
            test_doc = {"test": "connection", "timestamp": "2024-01-01"}
            result = await test_collection.insert_one(test_doc)
            print(f"   ✅ 写入测试成功: 文档ID {result.inserted_id}")
            
            # 读取测试文档
            found_doc = await test_collection.find_one({"_id": result.inserted_id})
            if found_doc:
                print(f"   ✅ 读取测试成功")
            
            # 删除测试文档
            await test_collection.delete_one({"_id": result.inserted_id})
            print(f"   ✅ 删除测试成功")
            
        except Exception as e:
            print(f"   ❌ 写入测试失败: {e}")
        
        # 关闭连接
        client.close()
        
        print(f"\n" + "=" * 60)
        print("✅ MongoDB连接测试完成")
        print("=" * 60)
        
        return True
        
    except pymongo.errors.ServerSelectionTimeoutError:
        print("❌ 连接超时: 无法连接到MongoDB服务器")
        print("   请检查:")
        print("   - MongoDB服务是否启动")
        print("   - 网络连接是否正常")
        print("   - 主机地址和端口是否正确")
        return False
        
    except pymongo.errors.OperationFailure as e:
        print(f"❌ 认证失败: {e}")
        print("   请检查:")
        print("   - 用户名和密码是否正确")
        print("   - 认证数据库是否正确")
        print("   - 用户是否有足够的权限")
        return False
        
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False


def test_pymongo_sync():
    """使用同步pymongo测试连接"""
    print(f"\n🔄 使用同步连接测试...")
    
    try:
        # 创建同步客户端
        client = pymongo.MongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=5000)
        
        # 测试连接
        client.admin.command('ping')
        print("   ✅ 同步连接成功")
        
        # 获取数据库列表
        databases = client.list_database_names()
        print(f"   📚 发现 {len(databases)} 个数据库")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"   ❌ 同步连接失败: {e}")
        return False


async def main():
    """主函数"""
    print("MongoDB连接测试工具")
    print("用于验证MongoDB配置是否正确\n")
    
    # 异步连接测试
    async_success = await test_mongodb_connection()
    
    # 同步连接测试
    sync_success = test_pymongo_sync()
    
    if async_success and sync_success:
        print(f"\n🎉 所有测试通过！MongoDB配置正确。")
        print(f"\n📖 接下来你可以:")
        print("1. 启用MongoDB: 在配置中设置 USE_MONGO=true")
        print("2. 启动服务器: python start_server.py")
        print("3. 查看MongoDB数据源: 访问数据源管理API")
        return 0
    else:
        print(f"\n❌ 部分测试失败，请检查MongoDB配置。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())

#!/usr/bin/env python3
"""
日志系统测试脚本
测试各种日志级别和功能
"""
import sys
import os
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_logging_system():
    """测试日志系统"""
    print("🧪 开始测试日志系统...")
    
    try:
        # 导入日志模块
        from app.core.logging import (
            setup_app_logging, get_module_logger, 
            info, debug, warning, error, success, critical
        )
        
        print("✅ 日志模块导入成功")
        
        # 初始化日志系统
        setup_app_logging()
        print("✅ 日志系统初始化成功")
        
        # 测试全局日志函数
        print("\n📝 测试全局日志函数:")
        debug("这是一条 DEBUG 级别的日志")
        info("这是一条 INFO 级别的日志")
        success("这是一条 SUCCESS 级别的日志")
        warning("这是一条 WARNING 级别的日志")
        error("这是一条 ERROR 级别的日志")
        critical("这是一条 CRITICAL 级别的日志")
        
        # 测试模块级日志
        print("\n📝 测试模块级日志:")
        module_logger = get_module_logger("test_module")
        module_logger.info("模块级日志测试")
        module_logger.debug("调试信息")
        module_logger.warning("警告信息")
        module_logger.error("错误信息")
        
        # 测试异常日志
        print("\n📝 测试异常日志:")
        try:
            raise ValueError("这是一个测试异常")
        except Exception as e:
            module_logger.exception("捕获到异常")
        
        # 测试日志文件
        log_file = Path("logs/app.log")
        if log_file.exists():
            print(f"✅ 日志文件已创建: {log_file.absolute()}")
            print(f"📄 日志文件大小: {log_file.stat().st_size} 字节")
        else:
            print("⚠️  日志文件未找到")
        
        print("\n🎉 日志系统测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 日志系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loading():
    """测试配置加载"""
    print("\n🔧 测试配置加载...")
    
    try:
        from app.config import settings
        
        print(f"  📋 项目名称: {settings.PROJECT_NAME}")
        print(f"  📊 日志级别: {settings.LOG_LEVEL}")
        print(f"  📁 日志文件: {settings.LOG_FILE_PATH}")
        print(f"  🔄 日志轮转: {settings.LOG_ROTATION}")
        print(f"  📅 日志保留: {settings.LOG_RETENTION}")
        print(f"  🐛 调试模式: {settings.DEBUG}")
        
        print("✅ 配置加载成功")
        return True
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False


def test_service_logging():
    """测试服务日志"""
    print("\n🚀 测试服务启动日志...")
    
    try:
        # 模拟服务启动日志
        from app.core.logging import get_module_logger
        
        service_logger = get_module_logger("test_service")
        
        service_logger.info("🚀 服务启动中...")
        service_logger.debug("加载配置文件")
        service_logger.info("✅ 数据库连接成功")
        service_logger.success("🎯 vLLM 服务连接成功")
        service_logger.warning("⚠️  某些功能可能不可用")
        service_logger.success("🎉 服务启动完成!")
        
        print("✅ 服务日志测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 服务日志测试失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 Model Control AI System - 日志系统测试")
    print("=" * 60)
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 运行测试
    tests = [
        ("配置加载测试", test_config_loading),
        ("日志系统测试", test_logging_system),
        ("服务日志测试", test_service_logging),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'=' * 20} {test_name} {'=' * 20}")
        result = test_func()
        results.append((test_name, result))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有测试都通过了!")
        print("💡 提示:")
        print("  - 日志文件保存在 logs/ 目录")
        print("  - 可以通过 .env 文件配置日志级别")
        print("  - 支持的日志级别: TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL")
    else:
        print("\n⚠️  部分测试失败，请检查配置")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

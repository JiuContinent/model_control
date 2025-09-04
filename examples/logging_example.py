#!/usr/bin/env python3
"""
日志系统使用示例
演示如何在项目中使用日志功能
"""
import sys
from pathlib import Path

# 添加 src 到路径
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# 导入日志模块
from app.core.logging import get_module_logger, info, debug, warning, error, success

def example_service_startup():
    """模拟服务启动过程"""
    logger = get_module_logger(__name__)
    
    logger.info("🚀 开始启动服务...")
    
    # 模拟各种启动步骤
    try:
        logger.debug("加载配置文件")
        # 模拟配置加载
        config = {"database": "mongodb://localhost", "port": 2000}
        logger.success("✅ 配置加载成功")
        
        logger.info("连接数据库...")
        # 模拟数据库连接
        logger.success("✅ 数据库连接成功")
        
        logger.info("初始化 vLLM 客户端...")
        # 模拟 vLLM 连接
        logger.success("✅ vLLM 客户端初始化成功")
        
        logger.info("启动 API 服务器...")
        logger.success(f"✅ API 服务器启动成功，监听端口 {config['port']}")
        
        logger.success("🎉 所有服务启动完成！")
        
    except Exception as e:
        logger.error(f"❌ 服务启动失败: {e}")
        raise


def example_api_request():
    """模拟 API 请求处理"""
    logger = get_module_logger("api_handler")
    
    logger.info("收到 API 请求: POST /api/v1/llm/chat/completions")
    
    try:
        # 模拟请求验证
        logger.debug("验证请求参数")
        
        # 模拟调用 vLLM
        logger.info("调用 vLLM 服务...")
        logger.debug("发送消息到 vLLM: 你好，请介绍一下你自己")
        
        # 模拟成功响应
        response = {"content": "您好！我是一个AI助手..."}
        logger.success(f"✅ vLLM 响应成功，长度: {len(response['content'])} 字符")
        
        logger.info("API 请求处理完成")
        return response
        
    except ConnectionError as e:
        logger.error(f"❌ vLLM 服务连接失败: {e}")
        raise
    except Exception as e:
        logger.exception("❌ API 请求处理异常")
        raise


def example_error_handling():
    """演示错误处理和日志记录"""
    logger = get_module_logger("error_example")
    
    logger.info("演示错误处理...")
    
    # 1. 警告级别的问题
    logger.warning("⚠️  检测到内存使用率较高: 85%")
    
    # 2. 可恢复的错误
    try:
        # 模拟网络超时
        raise TimeoutError("网络请求超时")
    except TimeoutError as e:
        logger.error(f"❌ 网络请求失败，使用缓存数据: {e}")
        logger.info("✅ 已切换到缓存数据")
    
    # 3. 严重错误
    try:
        # 模拟严重错误
        raise RuntimeError("系统内存不足")
    except RuntimeError as e:
        logger.critical(f"🚨 系统严重错误: {e}")
        logger.critical("系统将尝试释放资源")


def example_batch_processing():
    """演示批量处理中的日志使用"""
    logger = get_module_logger("batch_processor")
    
    items = list(range(100))  # 模拟 100 个任务
    batch_size = 20
    
    logger.info(f"开始批量处理: {len(items)} 个任务")
    
    processed = 0
    errors = 0
    
    for i, item in enumerate(items):
        try:
            # 模拟处理任务
            if item % 15 == 0:  # 模拟一些任务失败
                raise ValueError(f"任务 {item} 处理失败")
            
            processed += 1
            
            # 定期输出进度
            if (i + 1) % batch_size == 0:
                logger.info(f"📊 处理进度: {i + 1}/{len(items)} ({((i + 1)/len(items)*100):.1f}%)")
                
        except Exception as e:
            errors += 1
            logger.error(f"任务 {item} 失败: {e}")
    
    # 输出最终统计
    if errors == 0:
        logger.success(f"🎉 批量处理完成: {processed} 个任务全部成功")
    else:
        logger.warning(f"⚠️  批量处理完成: 成功 {processed}, 失败 {errors}")


def main():
    """主函数，演示各种日志使用场景"""
    print("=" * 60)
    print("📝 Model Control AI System - 日志使用示例")
    print("=" * 60)
    
    # 使用全局日志函数
    info("🎯 开始日志示例演示")
    
    try:
        # 1. 服务启动日志
        print("\n1️⃣  服务启动日志示例:")
        example_service_startup()
        
        # 2. API 请求日志
        print("\n2️⃣  API 请求日志示例:")
        example_api_request()
        
        # 3. 错误处理日志
        print("\n3️⃣  错误处理日志示例:")
        example_error_handling()
        
        # 4. 批量处理日志
        print("\n4️⃣  批量处理日志示例:")
        example_batch_processing()
        
        success("🎉 所有日志示例演示完成!")
        
    except Exception as e:
        error(f"❌ 示例演示过程中出现错误: {e}")
    
    # 显示日志文件信息
    log_file = Path("logs/app.log")
    if log_file.exists():
        info(f"📄 日志已保存到: {log_file.absolute()}")
        info(f"📊 日志文件大小: {log_file.stat().st_size} 字节")
    
    print("\n💡 提示:")
    print("  - 查看完整日志: tail -f logs/app.log")
    print("  - 搜索错误日志: grep 'ERROR' logs/app.log")
    print("  - 调整日志级别: 修改 .env 文件中的 LOG_LEVEL")


if __name__ == "__main__":
    main()

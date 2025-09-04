"""
统一的日志配置系统
使用 loguru 提供类似 Java 的日志功能
"""
import os
import sys
from pathlib import Path
from loguru import logger
from typing import Optional, Dict, Any

from app.config import settings


class LogConfig:
    """日志配置类"""
    
    # 日志级别映射
    LOG_LEVELS = {
        "TRACE": 5,
        "DEBUG": 10,
        "INFO": 20,
        "SUCCESS": 25,
        "WARNING": 30,
        "ERROR": 40,
        "CRITICAL": 50
    }
    
    # 日志格式
    DEFAULT_FORMAT = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # 文件日志格式（更详细）
    FILE_FORMAT = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{process.id}:{thread.id} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    @classmethod
    def setup_logging(
        cls,
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_file_path: Optional[str] = None,
        log_rotation: str = "10 MB",
        log_retention: str = "7 days",
        enable_console: bool = True,
        console_format: Optional[str] = None,
        file_format: Optional[str] = None
    ) -> None:
        """
        设置日志配置
        
        Args:
            log_level: 日志级别 (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
            log_to_file: 是否输出到文件
            log_file_path: 日志文件路径，默认为 logs/app.log
            log_rotation: 日志轮转大小
            log_retention: 日志保留时间
            enable_console: 是否启用控制台输出
            console_format: 控制台日志格式
            file_format: 文件日志格式
        """
        # 移除默认的处理器
        logger.remove()
        
        # 设置日志级别
        log_level = log_level.upper()
        if log_level not in cls.LOG_LEVELS:
            log_level = "INFO"
        
        # 控制台输出
        if enable_console:
            logger.add(
                sys.stderr,
                format=console_format or cls.DEFAULT_FORMAT,
                level=log_level,
                colorize=True,
                backtrace=True,
                diagnose=True
            )
        
        # 文件输出
        if log_to_file:
            if not log_file_path:
                # 创建日志目录
                log_dir = Path("logs")
                log_dir.mkdir(exist_ok=True)
                log_file_path = log_dir / "app.log"
            
            logger.add(
                log_file_path,
                format=file_format or cls.FILE_FORMAT,
                level=log_level,
                rotation=log_rotation,
                retention=log_retention,
                compression="zip",
                backtrace=True,
                diagnose=True,
                encoding="utf-8"
            )
        
        # 添加过滤器，过滤掉一些噪音日志
        cls._add_filters()
        
        logger.info(f"日志系统已初始化 - 级别: {log_level}, 控制台: {enable_console}, 文件: {log_to_file}")
    
    @classmethod
    def _add_filters(cls):
        """添加日志过滤器"""
        def filter_uvicorn(record):
            """过滤 uvicorn 的一些噪音日志"""
            if record["name"].startswith("uvicorn.access"):
                # 只记录错误级别的访问日志
                return record["level"].no >= logger.level("WARNING").no
            return True
        
        # 注意：loguru 的过滤器需要在添加处理器时设置
        # 这里只是示例，实际使用时需要在 add() 方法中使用 filter 参数
    
    @classmethod
    def get_logger(cls, name: str = None) -> Any:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称，通常使用 __name__
            
        Returns:
            loguru.Logger: 日志记录器实例
        """
        if name:
            return logger.bind(name=name)
        return logger


def setup_app_logging():
    """设置应用程序日志"""
    # 从配置中获取日志设置
    log_level = getattr(settings, 'LOG_LEVEL', 'INFO').upper()
    debug_mode = getattr(settings, 'DEBUG', False)
    
    # 如果是调试模式，使用 DEBUG 级别
    if debug_mode:
        log_level = 'DEBUG'
    
    LogConfig.setup_logging(
        log_level=log_level,
        log_to_file=True,
        enable_console=True,
        log_rotation="50 MB",
        log_retention="30 days"
    )


# 创建全局日志记录器实例
def get_logger(name: str = None):
    """获取日志记录器的便捷函数"""
    return LogConfig.get_logger(name)


# 为了兼容现有代码，提供类似 Java 的日志方法
class Logger:
    """Java 风格的日志记录器包装类"""
    
    def __init__(self, name: str = None):
        self._logger = get_logger(name)
    
    def trace(self, message: str, *args, **kwargs):
        """TRACE 级别日志"""
        self._logger.trace(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """DEBUG 级别日志"""
        self._logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """INFO 级别日志"""
        self._logger.info(message, *args, **kwargs)
    
    def success(self, message: str, *args, **kwargs):
        """SUCCESS 级别日志"""
        self._logger.success(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """WARNING 级别日志"""
        self._logger.warning(message, *args, **kwargs)
    
    def warn(self, message: str, *args, **kwargs):
        """WARNING 级别日志 (别名)"""
        self.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """ERROR 级别日志"""
        self._logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """CRITICAL 级别日志"""
        self._logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """记录异常日志"""
        self._logger.exception(message, *args, **kwargs)


# 创建默认的日志记录器实例
default_logger = Logger()

# 提供便捷的全局函数
def trace(message: str, *args, **kwargs):
    """TRACE 级别日志"""
    default_logger.trace(message, *args, **kwargs)

def debug(message: str, *args, **kwargs):
    """DEBUG 级别日志"""
    default_logger.debug(message, *args, **kwargs)

def info(message: str, *args, **kwargs):
    """INFO 级别日志"""
    default_logger.info(message, *args, **kwargs)

def success(message: str, *args, **kwargs):
    """SUCCESS 级别日志"""
    default_logger.success(message, *args, **kwargs)

def warning(message: str, *args, **kwargs):
    """WARNING 级别日志"""
    default_logger.warning(message, *args, **kwargs)

def warn(message: str, *args, **kwargs):
    """WARNING 级别日志 (别名)"""
    default_logger.warn(message, *args, **kwargs)

def error(message: str, *args, **kwargs):
    """ERROR 级别日志"""
    default_logger.error(message, *args, **kwargs)

def critical(message: str, *args, **kwargs):
    """CRITICAL 级别日志"""
    default_logger.critical(message, *args, **kwargs)

def exception(message: str, *args, **kwargs):
    """记录异常日志"""
    default_logger.exception(message, *args, **kwargs)


# 模块级别的便捷函数
def get_module_logger(module_name: str = None) -> Logger:
    """
    获取模块级别的日志记录器
    
    Args:
        module_name: 模块名称，通常传入 __name__
        
    Returns:
        Logger: 日志记录器实例
        
    Example:
        logger = get_module_logger(__name__)
        logger.info("This is an info message")
    """
    return Logger(module_name)


# 用于替换 print 语句的装饰器
def log_print_replacement(func):
    """
    装饰器：将函数中的 print 语句替换为日志记录
    注意：这只是一个示例，实际使用时需要手动替换 print 语句
    """
    def wrapper(*args, **kwargs):
        # 这里可以添加一些逻辑来捕获和转换 print 语句
        # 但更好的方式是直接在代码中替换 print 为日志调用
        return func(*args, **kwargs)
    return wrapper

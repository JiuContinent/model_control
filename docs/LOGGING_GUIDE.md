# 日志系统使用指南

## 概述

本项目使用 `loguru` 库实现了类似 Java 的日志功能，支持多种日志级别、文件输出、日志轮转等功能。

## 日志级别

支持以下日志级别（从低到高）：

- `TRACE` - 最详细的调试信息
- `DEBUG` - 调试信息
- `INFO` - 一般信息
- `SUCCESS` - 成功操作信息
- `WARNING` - 警告信息
- `ERROR` - 错误信息
- `CRITICAL` - 严重错误信息

## 使用方法

### 1. 全局日志函数（推荐）

```python
from app.core.logging import info, debug, warning, error, success, critical

# 使用不同级别的日志
debug("这是调试信息")
info("这是一般信息")
success("操作成功!")
warning("这是警告信息")
error("这是错误信息")
critical("这是严重错误")
```

### 2. 模块级日志记录器

```python
from app.core.logging import get_module_logger

# 获取当前模块的日志记录器
logger = get_module_logger(__name__)

# 使用日志记录器
logger.info("模块初始化完成")
logger.error("模块发生错误")
```

### 3. Java 风格的日志记录器

```python
from app.core.logging import Logger

# 创建日志记录器
logger = Logger(__name__)

# 类似 Java 的使用方式
logger.info("这是信息日志")
logger.debug("这是调试日志")
logger.warn("这是警告日志")  # 或 logger.warning()
logger.error("这是错误日志")
```

### 4. 异常日志

```python
from app.core.logging import get_module_logger

logger = get_module_logger(__name__)

try:
    # 一些可能出错的代码
    result = 1 / 0
except Exception as e:
    # 记录异常信息，包含完整的堆栈跟踪
    logger.exception("计算出现异常")
    # 或者
    logger.error(f"计算出现异常: {e}")
```

## 配置

### 1. 环境变量配置

在 `.env` 文件中配置日志：

```bash
# 日志级别
LOG_LEVEL=INFO

# 是否输出到文件
LOG_TO_FILE=true

# 日志文件路径
LOG_FILE_PATH=logs/app.log

# 日志文件轮转大小
LOG_ROTATION=50 MB

# 日志文件保留时间
LOG_RETENTION=30 days

# 调试模式
DEBUG=false
```

### 2. 代码配置

```python
from app.core.logging import LogConfig

# 自定义日志配置
LogConfig.setup_logging(
    log_level="DEBUG",
    log_to_file=True,
    log_file_path="logs/custom.log",
    log_rotation="100 MB",
    log_retention="7 days"
)
```

## 日志格式

### 控制台输出格式
```
2025-09-04 18:30:15.123 | INFO     | app.main:startup_event:69 | 🚀 Model Control AI System started successfully!
```

### 文件输出格式
```
2025-09-04 18:30:15.123 | INFO     | 12345:67890 | app.main:startup_event:69 | 🚀 Model Control AI System started successfully!
```

## 最佳实践

### 1. 选择合适的日志级别

```python
from app.core.logging import get_module_logger

logger = get_module_logger(__name__)

# DEBUG - 详细的调试信息，生产环境不显示
logger.debug("处理用户请求: user_id=123")

# INFO - 一般信息，记录重要操作
logger.info("用户登录成功: user_id=123")

# SUCCESS - 成功操作，突出显示
logger.success("数据同步完成")

# WARNING - 警告，不影响功能但需要注意
logger.warning("API 响应时间较慢: 2.5s")

# ERROR - 错误，需要处理但不会崩溃
logger.error("连接数据库失败，使用缓存数据")

# CRITICAL - 严重错误，可能导致系统崩溃
logger.critical("内存不足，系统即将关闭")
```

### 2. 使用结构化日志

```python
# 好的做法：包含上下文信息
logger.info(f"用户操作: user_id={user_id}, action={action}, result={result}")

# 更好的做法：使用字典传递结构化数据
logger.info("用户操作完成", extra={
    "user_id": user_id,
    "action": action,
    "result": result,
    "duration": duration_ms
})
```

### 3. 异常处理

```python
try:
    # 业务逻辑
    result = process_data(data)
    logger.success(f"数据处理完成: {len(result)} 条记录")
except ValueError as e:
    logger.error(f"数据格式错误: {e}")
    raise
except Exception as e:
    logger.exception("数据处理失败")
    raise
```

### 4. 性能考虑

```python
# 避免在循环中使用过多日志
for item in large_list:
    # 不好：会产生大量日志
    # logger.debug(f"处理项目: {item}")
    
    process_item(item)

# 好：定期输出进度
batch_size = 100
for i, item in enumerate(large_list):
    process_item(item)
    if i % batch_size == 0:
        logger.info(f"处理进度: {i}/{len(large_list)}")
```

## 日志文件管理

### 1. 日志轮转

日志文件会根据配置自动轮转：

- 当文件大小超过 `LOG_ROTATION` 设置时创建新文件
- 旧文件会被压缩为 zip 格式
- 超过 `LOG_RETENTION` 时间的文件会被自动删除

### 2. 日志文件位置

- 默认位置：`logs/app.log`
- 轮转文件：`logs/app.log.2025-09-04_18-30-15_123456.zip`

### 3. 查看日志

```bash
# 查看最新日志
tail -f logs/app.log

# 搜索错误日志
grep "ERROR" logs/app.log

# 查看特定时间的日志
grep "2025-09-04 18:" logs/app.log
```

## 迁移指南

### 从 print 语句迁移

```python
# 旧代码
print("系统启动中...")
print(f"错误: {error}")

# 新代码
from app.core.logging import info, error

info("系统启动中...")
error(f"错误: {error}")
```

### 从其他日志库迁移

```python
# 从 logging 模块迁移
import logging
logging.info("信息")

# 迁移到 loguru
from app.core.logging import info
info("信息")
```

## 故障排除

### 1. 日志文件未创建

检查：
- `logs/` 目录是否存在且有写权限
- `LOG_TO_FILE` 配置是否为 `true`
- `LOG_FILE_PATH` 路径是否正确

### 2. 日志级别不生效

检查：
- `.env` 文件中的 `LOG_LEVEL` 设置
- 确保日志级别大小写正确
- 重启应用使配置生效

### 3. 日志格式问题

可以通过代码自定义格式：

```python
from app.core.logging import LogConfig

LogConfig.setup_logging(
    console_format="<green>{time}</green> | <level>{level}</level> | {message}",
    file_format="{time} | {level} | {message}"
)
```

## 性能优化

### 1. 条件日志

```python
# 避免不必要的字符串格式化
if logger._logger.level("DEBUG").no >= logger._logger.level(LOG_LEVEL).no:
    logger.debug(f"复杂的调试信息: {expensive_operation()}")
```

### 2. 异步日志

loguru 默认是同步的，如果需要异步可以配置：

```python
from loguru import logger

# 异步写入文件
logger.add("logs/async.log", enqueue=True)
```

## 监控和告警

### 1. 错误日志监控

可以配置日志监控系统来监控 ERROR 和 CRITICAL 级别的日志。

### 2. 日志统计

```python
# 可以添加钩子来统计日志
from collections import Counter

log_stats = Counter()

def count_logs(record):
    log_stats[record["level"].name] += 1
    return record

logger.add(count_logs, format="{message}")
```

## 示例代码

完整的使用示例：

```python
from app.core.logging import get_module_logger

class UserService:
    def __init__(self):
        self.logger = get_module_logger(__name__)
        self.logger.info("UserService 初始化完成")
    
    def create_user(self, user_data):
        self.logger.debug(f"创建用户请求: {user_data}")
        
        try:
            # 验证数据
            if not user_data.get('email'):
                self.logger.warning("用户数据缺少邮箱字段")
                raise ValueError("邮箱是必填字段")
            
            # 创建用户
            user = self._save_user(user_data)
            self.logger.success(f"用户创建成功: user_id={user.id}")
            
            return user
            
        except Exception as e:
            self.logger.error(f"用户创建失败: {e}")
            raise
    
    def _save_user(self, user_data):
        # 模拟保存用户
        self.logger.debug("保存用户到数据库")
        # ... 实际保存逻辑
        return {"id": 123, "email": user_data['email']}
```

这样就完成了从 `print` 语句到专业日志系统的迁移！

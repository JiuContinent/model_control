# MySQL多数据源快速开始指南

## 🚀 快速开始

本指南将帮您快速集成和使用MySQL多数据源功能。

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

新增的MySQL相关依赖：
- `aiomysql==0.2.0` - 异步MySQL连接器
- `sqlalchemy==2.0.23` - ORM框架
- `alembic==1.13.0` - 数据库迁移工具

### 2. 配置MySQL

创建 `src/app/.env` 文件：

```env
# MySQL设置
USE_MYSQL=true
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_CHARSET=utf8mb4

# 多租户数据库
MYSQL_TENANT_2_DB=tenant_2
MYSQL_TENANT_3_DB=tenant_3
MYSQL_RUOYI_VUE_PRO_DB=ruoyi_vue_pro

# 默认数据库
MYSQL_DEFAULT_DB=tenant_2
```

### 3. 初始化数据库

```bash
cd scripts
python init_mysql_databases.py
```

此脚本将：
- ✅ 创建三个数据库
- ✅ 创建所需的数据表
- ✅ 插入示例数据

### 4. 测试集成

```bash
cd scripts
python test_mysql_integration.py
```

验证所有功能是否正常工作。

### 5. 启动服务

```bash
python start_server.py
```

服务启动后访问：
- API文档: http://localhost:2000/docs
- MySQL管理: http://localhost:2000/api/v1/mysql-datasource/sources

## 📊 数据源概览

| 数据源 | 数据库名 | 用途 | 表类型 |
|--------|----------|------|--------|
| tenant_2 | tenant_2 | 租户2 | 租户表 |
| tenant_3 | tenant_3 | 租户3 | 租户表 |
| ruoyi_vue_pro | ruoyi_vue_pro | 若依系统 | 若依表 |

## 🔧 主要API接口

### 查看所有数据源
```http
GET /api/v1/mysql-datasource/sources
```

### 切换数据源
```http
POST /api/v1/mysql-datasource/switch
{
    "source_name": "tenant_2"
}
```

### 查看当前数据源
```http
GET /api/v1/mysql-datasource/current
```

### 健康检查
```http
GET /api/v1/mysql-datasource/health
```

## 💻 代码示例

### 基本使用

```python
from app.db.mysql_multi import get_mysql_db, switch_mysql_source

# 切换数据源
await switch_mysql_source("tenant_2")

# 使用数据库
async with get_mysql_db() as session:
    result = await session.execute("SELECT * FROM tenant_users")
    users = result.fetchall()
```

### 临时切换

```python
from app.db.mysql_multi import mysql_manager

# 临时使用其他数据源
async with mysql_manager.use_source("ruoyi_vue_pro") as session:
    result = await session.execute("SELECT * FROM ruoyi_users")
    users = result.fetchall()
# 自动切换回原数据源
```

## 🎯 实际应用场景

### 1. 多租户系统
```python
# 为不同租户使用不同数据库
async def get_tenant_data(tenant_id: int):
    source_name = f"tenant_{tenant_id}"
    await switch_mysql_source(source_name)
    
    async with get_mysql_db() as session:
        # 查询租户专属数据
        pass
```

### 2. 系统集成
```python
# 与若依系统集成
async def sync_with_ruoyi():
    await switch_mysql_source("ruoyi_vue_pro")
    
    async with get_mysql_db() as session:
        # 同步若依用户数据
        pass
```

### 3. 数据迁移
```python
# 跨数据源数据迁移
async def migrate_data():
    # 从源数据库读取
    async with mysql_manager.use_source("tenant_2") as source_session:
        data = await source_session.execute("SELECT * FROM tenant_users")
        users = data.fetchall()
    
    # 写入目标数据库
    async with mysql_manager.use_source("tenant_3") as target_session:
        # 插入数据
        pass
```

## 🔍 故障排除

### 连接失败
```bash
# 检查MySQL服务
sudo systemctl status mysql

# 测试连接
mysql -h localhost -u root -p
```

### 权限问题
```sql
-- 为用户授权
GRANT ALL PRIVILEGES ON *.* TO 'root'@'localhost';
FLUSH PRIVILEGES;
```

### 重新初始化
```bash
# 删除数据库重新创建
mysql -u root -p -e "DROP DATABASE IF EXISTS tenant_2; DROP DATABASE IF EXISTS tenant_3; DROP DATABASE IF EXISTS ruoyi_vue_pro;"

# 重新运行初始化
python scripts/init_mysql_databases.py
```

## 📈 性能优化

### 连接池配置
在 `mysql_multi.py` 中调整：
```python
engine = create_async_engine(
    connection_url,
    pool_size=20,        # 增加连接池大小
    max_overflow=30,     # 增加溢出连接数
    pool_pre_ping=True,  # 连接预检查
    pool_recycle=3600    # 连接回收时间
)
```

### 查询优化
- 使用适当的索引
- 避免SELECT *
- 使用LIMIT限制结果集
- 合理使用事务

## 📝 下一步

1. **运行示例**: `python examples/mysql_usage_example.py`
2. **阅读完整文档**: `MYSQL_MULTI_DATASOURCE_README.md`
3. **自定义数据模型**: 编辑 `src/app/models/mysql_models.py`
4. **添加新数据源**: 修改配置并重新初始化

## ❓ 需要帮助？

- 查看API文档: http://localhost:2000/docs
- 检查日志输出
- 运行测试脚本验证配置
- 查看完整的使用示例

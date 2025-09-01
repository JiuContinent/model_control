# MySQL多数据源支持文档

## 概述

本项目已集成MySQL多数据源支持，可以在同一个MySQL服务中管理多个数据库，包括：
- `tenant_2` - 租户2数据库
- `tenant_3` - 租户3数据库  
- `ruoyi_vue_pro` - 若依Vue Pro数据库

支持动态切换不同的数据源，每个数据源可以有不同的表结构和数据模型。

## 功能特性

- ✅ 多租户数据库支持
- ✅ 动态数据源切换
- ✅ 异步数据库操作
- ✅ 连接池管理
- ✅ 事务支持
- ✅ 若依Vue Pro兼容
- ✅ RESTful API管理接口
- ✅ 健康检查
- ✅ 表结构查询

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置MySQL

在 `src/app/.env` 文件中配置MySQL连接信息：

```env
# MySQL Settings
USE_MYSQL=true
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_CHARSET=utf8mb4

# MySQL Multi-tenant Database Configuration
MYSQL_TENANT_2_DB=tenant_2
MYSQL_TENANT_3_DB=tenant_3
MYSQL_RUOYI_VUE_PRO_DB=ruoyi_vue_pro

# Default MySQL Database
MYSQL_DEFAULT_DB=tenant_2
```

### 3. 初始化数据库

运行初始化脚本创建数据库和表：

```bash
cd scripts
python init_mysql_databases.py
```

### 4. 启动服务

```bash
python start_server.py
```

## API接口

### 数据源管理

#### 获取所有数据源
```http
GET /api/v1/mysql-datasource/sources
```

#### 获取当前数据源
```http
GET /api/v1/mysql-datasource/current
```

#### 切换数据源
```http
POST /api/v1/mysql-datasource/switch
Content-Type: application/json

{
    "source_name": "tenant_2"
}
```

#### 测试连接
```http
POST /api/v1/mysql-datasource/test-connection?source_name=tenant_2
```

### 表管理

#### 创建表
```http
POST /api/v1/mysql-datasource/create-tables
Content-Type: application/json

{
    "source_name": "tenant_2",
    "table_type": "tenant"
}
```

#### 获取表列表
```http
GET /api/v1/mysql-datasource/tables?source_name=tenant_2
```

#### 获取表结构
```http
GET /api/v1/mysql-datasource/table/tenant_users/structure?source_name=tenant_2
```

### 数据操作

#### 执行SQL查询
```http
POST /api/v1/mysql-datasource/execute-sql
Content-Type: application/json

{
    "sql": "SELECT * FROM tenant_users LIMIT 10",
    "source_name": "tenant_2"
}
```

#### 健康检查
```http
GET /api/v1/mysql-datasource/health
```

## 数据模型

### 租户数据模型 (tenant_2, tenant_3)

- `tenant_users` - 租户用户表
- `tenant_roles` - 租户角色表
- `tenant_menus` - 租户菜单表
- `system_logs` - 系统日志表
- `ai_detection_records` - AI检测记录表
- `vehicle_data` - 车辆数据表

### 若依Vue Pro数据模型 (ruoyi_vue_pro)

- `ruoyi_users` - 若依用户表
- `ruoyi_roles` - 若依角色表
- `ruoyi_menus` - 若依菜单表

## 代码示例

### Python代码中使用

```python
from app.db.mysql_multi import get_mysql_db, switch_mysql_source
from app.models.mysql_models import TenantUser

# 切换数据源
await switch_mysql_source("tenant_2")

# 使用当前数据源
async with get_mysql_db() as session:
    users = await session.execute("SELECT * FROM tenant_users")
    result = users.fetchall()

# 使用指定数据源
async with get_mysql_db("ruoyi_vue_pro") as session:
    users = await session.execute("SELECT * FROM ruoyi_users")
    result = users.fetchall()

# 临时切换数据源
from app.db.mysql_multi import mysql_manager

async with mysql_manager.use_source("tenant_3") as session:
    # 在这个上下文中使用tenant_3数据源
    user = TenantUser(username="test", tenant_id=3)
    session.add(user)
    await session.commit()
# 自动切换回原来的数据源
```

### 事务支持

```python
async with get_mysql_db("tenant_2") as session:
    try:
        # 数据库操作
        user = TenantUser(username="test", tenant_id=2)
        session.add(user)
        
        role = TenantRole(name="test_role", tenant_id=2)
        session.add(role)
        
        # 事务会自动提交
    except Exception:
        # 出错时会自动回滚
        raise
```

## 注意事项

1. **数据库连接**: 确保MySQL服务正在运行且配置正确
2. **权限**: 确保MySQL用户有创建数据库和表的权限
3. **字符集**: 推荐使用utf8mb4字符集支持完整的Unicode
4. **连接池**: 系统会自动管理连接池，无需手动关闭连接
5. **线程安全**: 所有操作都是异步线程安全的

## 故障排除

### 连接失败
- 检查MySQL服务是否启动
- 验证连接参数（主机、端口、用户名、密码）
- 确认防火墙设置

### 数据库不存在
- 运行初始化脚本: `python scripts/init_mysql_databases.py`
- 手动创建数据库

### 权限问题
- 确保MySQL用户有足够的权限
- 检查数据库和表的访问权限

### 性能优化
- 调整连接池大小配置
- 优化SQL查询
- 添加适当的索引

## 扩展支持

### 添加新的数据源

1. 在配置文件中添加新的数据库配置
2. 在 `mysql_manager.data_sources` 中添加数据源定义
3. 创建相应的数据模型
4. 运行初始化脚本

### 自定义数据模型

```python
from app.models.mysql_models import BaseModel
from sqlalchemy import Column, String

class CustomModel(BaseModel):
    __tablename__ = "custom_table"
    
    name = Column(String(100), nullable=False)
    description = Column(String(500))
```

## 版本信息

- MySQL: 8.0+
- Python: 3.11+
- SQLAlchemy: 2.0+
- aiomysql: 0.2.0+

## 更多信息

- API文档: http://localhost:2000/docs
- 健康检查: http://localhost:2000/api/v1/mysql-datasource/health
- 系统状态: http://localhost:2000/api/v1/status

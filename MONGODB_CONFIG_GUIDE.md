# MongoDB配置指南

## 📋 概述

本指南将帮助您正确配置MongoDB的账号密码，支持有认证和无认证两种模式。

## 🔧 配置方法

### 方法1: 在 `.env` 文件中配置

在 `src/app/.env` 文件中添加以下配置：

#### 有认证的MongoDB
```env
# MongoDB基本配置
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=your_username
MONGO_PASSWORD=your_password
MONGO_AUTH_DB=admin
MONGO_DB_NAME=model_control_db

# 多数据源数据库名
MAVLINK_MONGO_DB_NAME=model_control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=model_control_analytics
```

#### 无认证的MongoDB
```env
# MongoDB基本配置
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=
MONGO_PASSWORD=
MONGO_DB_NAME=model_control_db

# 多数据源数据库名
MAVLINK_MONGO_DB_NAME=model_control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=model_control_analytics
```

### 方法2: 通过环境变量

您也可以通过系统环境变量设置：

```bash
export MONGO_HOST=221.226.33.58
export MONGO_PORT=27017
export MONGO_USERNAME=your_username
export MONGO_PASSWORD=your_password
export MONGO_AUTH_DB=admin
```

## 🔒 常见MongoDB认证配置

### 1. 默认admin用户
```env
MONGO_USERNAME=admin
MONGO_PASSWORD=admin123
MONGO_AUTH_DB=admin
```

### 2. 自定义用户
```env
MONGO_USERNAME=myuser
MONGO_PASSWORD=mypassword
MONGO_AUTH_DB=mydb
```

### 3. 应用专用用户
```env
MONGO_USERNAME=model_control_user
MONGO_PASSWORD=secure_password
MONGO_AUTH_DB=admin
```

## 🔍 生成的连接URI

系统会根据您的配置自动生成连接URI：

### 有认证
```
mongodb://username:password@221.226.33.58:27017/admin
```

### 无认证
```
mongodb://221.226.33.58:27017/
```

## ✅ 测试连接

使用我们提供的测试脚本验证配置：

```bash
cd scripts
python test_mongodb_connection.py
```

测试脚本会：
- ✅ 验证连接是否成功
- ✅ 显示服务器信息
- ✅ 列出可用数据库
- ✅ 测试读写权限

## 🚨 常见问题

### 1. 认证失败
```
❌ 认证失败: Authentication failed
```

**解决方案:**
- 检查用户名和密码是否正确
- 确认认证数据库是否正确（通常是`admin`）
- 验证用户是否存在且有相应权限

### 2. 连接超时
```
❌ 连接超时: No servers available
```

**解决方案:**
- 检查MongoDB服务是否启动
- 验证网络连接
- 确认主机地址和端口

### 3. 权限不足
```
❌ 权限不足: not authorized
```

**解决方案:**
- 为用户分配适当的角色
- 检查数据库访问权限

## 📚 MongoDB用户管理

### 创建用户（在MongoDB中执行）

```javascript
// 连接到MongoDB
use admin

// 创建管理员用户
db.createUser({
  user: "admin",
  pwd: "admin123",
  roles: [
    { role: "userAdminAnyDatabase", db: "admin" },
    { role: "readWriteAnyDatabase", db: "admin" }
  ]
})

// 创建应用用户
db.createUser({
  user: "model_control_user",
  pwd: "secure_password",
  roles: [
    { role: "readWrite", db: "model_control_db" },
    { role: "readWrite", db: "model_control_mavlink" },
    { role: "readWrite", db: "model_control_chat" },
    { role: "readWrite", db: "model_control_analytics" }
  ]
})
```

### 查看用户

```javascript
// 查看所有用户
db.getUsers()

// 查看特定用户
db.getUser("model_control_user")
```

## 🔐 安全建议

1. **使用强密码**: 包含大小写字母、数字和特殊字符
2. **最小权限原则**: 只授予必要的数据库权限
3. **网络安全**: 限制MongoDB的网络访问
4. **定期更新**: 定期更换密码
5. **连接加密**: 生产环境中启用TLS/SSL

## 📖 配置示例

### 开发环境
```env
USE_MONGO=true
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USERNAME=dev_user
MONGO_PASSWORD=dev_password
MONGO_AUTH_DB=admin
```

### 生产环境
```env
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=prod_user
MONGO_PASSWORD=very_secure_password_123!
MONGO_AUTH_DB=admin
```

### 无认证环境（仅测试）
```env
USE_MONGO=true
MONGO_HOST=localhost
MONGO_PORT=27017
MONGO_USERNAME=
MONGO_PASSWORD=
```

## 🚀 下一步

1. **配置MongoDB**: 根据本指南设置账号密码
2. **测试连接**: 运行测试脚本验证配置
3. **启动服务**: `python start_server.py`
4. **查看文档**: 访问 http://localhost:2000/docs

现在您已经了解如何正确配置MongoDB的账号密码了！

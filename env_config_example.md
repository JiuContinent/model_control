# 环境配置示例

在 `src/app/.env` 文件中配置数据库连接信息：

## MongoDB配置

### 方式1: 有认证的MongoDB
```env
# MongoDB设置
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=your_mongodb_username
MONGO_PASSWORD=your_mongodb_password
MONGO_AUTH_DB=admin
MONGO_DB_NAME=model_control_db

# MongoDB多数据源数据库名
MAVLINK_MONGO_DB_NAME=model_control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=model_control_analytics
```

生成的连接URI: `mongodb://username:password@221.226.33.58:27017/admin`

### 方式2: 无认证的MongoDB
```env
# MongoDB设置
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=
MONGO_PASSWORD=
MONGO_DB_NAME=model_control_db
```

生成的连接URI: `mongodb://221.226.33.58:27017/`

## MySQL配置

```env
# MySQL设置
USE_MYSQL=true
MYSQL_HOST=221.226.33.58
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=RedFlym3y6s9@&#
MYSQL_CHARSET=utf8mb4

# MySQL多租户数据库配置
MYSQL_TENANT_2_DB=tenant_2
MYSQL_TENANT_3_DB=tenant_3
MYSQL_RUOYI_VUE_PRO_DB=ruoyi_vue_pro
MYSQL_DEFAULT_DB=tenant_2
```

## 完整配置示例

```env
# 项目基本设置
PROJECT_NAME=Model Control AI System

# MongoDB设置
USE_MONGO=true
MONGO_HOST=221.226.33.58
MONGO_PORT=27017
MONGO_USERNAME=admin
MONGO_PASSWORD=your_mongo_password
MONGO_AUTH_DB=admin
MONGO_DB_NAME=model_control_db
MAVLINK_MONGO_DB_NAME=model_control_mavlink
CHAT_MONGO_DB_NAME=model_control_chat
ANALYTICS_MONGO_DB_NAME=model_control_analytics

# MySQL设置
USE_MYSQL=true
MYSQL_HOST=221.226.33.58
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=RedFlym3y6s9@&#
MYSQL_CHARSET=utf8mb4
MYSQL_TENANT_2_DB=tenant_2
MYSQL_TENANT_3_DB=tenant_3
MYSQL_RUOYI_VUE_PRO_DB=ruoyi_vue_pro
MYSQL_DEFAULT_DB=tenant_2

# OpenAI设置（可选）
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
```

## 常见MongoDB认证配置

### 1. 默认admin用户
```env
MONGO_USERNAME=admin
MONGO_PASSWORD=your_admin_password
MONGO_AUTH_DB=admin
```

### 2. 自定义用户
```env
MONGO_USERNAME=myuser
MONGO_PASSWORD=mypassword
MONGO_AUTH_DB=myauthdb
```

### 3. 读写分离
```env
# 读写用户
MONGO_USERNAME=readwrite_user
MONGO_PASSWORD=rw_password
MONGO_AUTH_DB=admin
```

## 注意事项

1. **密码特殊字符**: 如果密码包含特殊字符，可能需要URL编码
2. **认证数据库**: 通常使用 `admin` 作为认证数据库
3. **连接测试**: 可以使用 MongoDB Compass 或命令行工具测试连接
4. **安全性**: 生产环境中请使用强密码并限制网络访问

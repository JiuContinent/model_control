# Model Control AI System

一个基于 FastAPI 的模型控制系统，集成 YOLOv11 AI 识别功能和 MAVLink 协议支持。

## 🚀 功能特性

- **YOLOv11 AI 目标检测**：支持单张图片和批量图片检测
- **MAVLink 协议支持**：接收和解析 MAVLink 二进制数据
- **多数据源管理**：支持 DJI、UE 等多个数据源
- **实时数据存储**：自动存储 MAVLink 消息到 MongoDB
- **RESTful API**：提供完整的 API 接口
- **异步处理**：高性能异步架构
- **日志系统**：完整的日志记录和监控

## 📁 项目结构

```
model_control/
├── src/
│   └── app/
│       ├── api/              # API 路由层
│       │   ├── ai.py         # AI 相关接口
│       │   ├── mavlink.py    # MAVLink 接口
│       │   ├── datasource.py # 数据源管理
│       │   └── upload.py     # 文件上传
│       ├── core/             # 核心模块
│       │   ├── constants.py  # 常量定义
│       │   ├── exceptions.py # 自定义异常
│       │   └── logging.py    # 日志配置
│       ├── services/         # 业务服务层
│       │   ├── ai_service.py # AI 服务
│       │   └── mavlink_service.py # MAVLink 服务
│       ├── utils/            # 工具模块
│       │   └── file_utils.py # 文件处理工具
│       ├── models/           # 数据模型
│       ├── db/               # 数据库连接
│       ├── mavlink/          # MAVLink 相关
│       ├── config.py         # 配置管理
│       └── main.py           # 应用入口
├── tests/                    # 测试文件
├── logs/                     # 日志文件
├── uploads/                  # 上传文件目录
├── models/                   # AI 模型文件
├── pyproject.toml           # 项目配置
├── docker-compose.yml       # Docker 配置
└── README.md               # 项目文档
```

## 🛠️ 快速开始

### 1. 环境要求

- Python 3.11+
- CUDA 支持（可选，用于 GPU 加速）

### 2. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd model_control

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -e .
```

### 3. 环境配置

创建 `.env` 文件并配置以下环境变量：

```env
# MongoDB 配置
MONGO_URI="mongodb://localhost:27017/"
MONGO_DB_NAME="model_control"

# AI 模型配置
AI_MODEL_PATH="models/yolov11.pt"
AI_CONFIDENCE_THRESHOLD=0.5
AI_IOU_THRESHOLD=0.45

# MAVLink 配置
MAVLINK_HOST="0.0.0.0"
MAVLINK_PORT=5760

# 日志配置
LOG_LEVEL="INFO"
```

### 4. 启动应用

```bash
# 开发模式启动
uvicorn app.main:app --reload --app-dir src

# 或直接运行
python src/app/main.py
```

### 5. 访问 API

- API 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc
- 健康检查：http://localhost:8000/health

## 🤖 AI 功能

### 单张图片检测

```bash
curl -X POST "http://localhost:8000/api/v1/ai/detect" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@image.jpg" \
  -F "confidence=0.5" \
  -F "iou_threshold=0.45"
```

### 批量图片检测

```bash
curl -X POST "http://localhost:8000/api/v1/ai/detect-batch" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@image1.jpg" \
  -F "files=@image2.jpg"
```

### 获取模型信息

```bash
curl "http://localhost:8000/api/v1/ai/model-info"
```

## 📡 MAVLink 功能

### 启动接收器

```bash
curl -X POST "http://localhost:8000/api/v1/mavlink/receiver/start" \
  -H "Content-Type: application/json" \
  -d '{"host": "0.0.0.0", "port": 5760}'
```

### 获取消息

```bash
curl "http://localhost:8000/api/v1/mavlink/messages?limit=100"
```

### 获取统计信息

```bash
curl "http://localhost:8000/api/v1/mavlink/statistics"
```

## 🗄️ 数据源管理

### 切换数据源

```bash
# 切换到 UE 数据源
curl -X POST "http://localhost:8000/api/v1/datasource/switch/ue"

# 查看当前数据源
curl "http://localhost:8000/api/v1/datasource/current"
```

## 🧪 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_ai_service.py

# 运行测试并生成覆盖率报告
pytest --cov=app tests/
```

## 🐳 Docker 部署

```bash
# 构建镜像
docker build -t model-control-ai .

# 运行容器
docker run -p 8000:8000 model-control-ai

# 使用 Docker Compose
docker-compose up -d
```

## 📊 监控和日志

- 应用日志：`logs/app.log`
- 错误日志：`logs/error.log`
- 日志轮转：每天轮转，保留30天

## 🔧 配置说明

### AI 模型配置

```python
AI_MODEL_CONFIG = {
    "yolov11": {
        "model_path": "models/yolov11.pt",
        "confidence_threshold": 0.5,
        "iou_threshold": 0.45,
        "max_det": 300,
        "classes": None,  # 检测所有类别
    }
}
```

### API 配置

```python
API_CONFIG = {
    "max_file_size": 100 * 1024 * 1024,  # 100MB
    "allowed_image_types": [".jpg", ".jpeg", ".png", ".bmp", ".tiff"],
    "max_batch_size": 10,
}
```

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系方式

- 项目维护者：[Jiu Continent]
- 邮箱：JiuContinent@gmail.com]
- 项目地址：[https://github.com/yourusername/model-control-ai]


## python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir src
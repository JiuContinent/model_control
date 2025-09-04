# 实时AI识别模块 (Real-time AI Recognition Module)

这是一个现代化的实时AI识别系统，支持多种流媒体协议（RTSP/RTMP）和YOLOv11模型变体。

##  功能特性

- **多种流媒体协议支持**: RTSP、RTMP、HTTP/HTTPS、本地文件
- **YOLOv11模型系列**: 支持从nano到extra-large的所有变体
- **GPU加速**: 自动检测CUDA/MPS，支持半精度推理
- **多GPU并行处理**: 自动负载均衡，支持2-8个GPU同时工作
- **异步处理**: 高性能异步架构，支持并发流处理
- **RESTful API**: 完整的REST API接口
- **实时结果流**: Server-Sent Events实时推送检测结果
- **可扩展架构**: 工厂模式支持自定义检测器和流提供者

##  系统要求

### 基础要求
- Python 3.11+
- 8GB+ RAM
- OpenCV 4.8+
- Ultralytics YOLOv11

### GPU加速 (推荐)
- NVIDIA GPU: CUDA 11.8+ 支持
- Apple Silicon: MPS 支持
- 至少4GB GPU内存
- **多GPU支持**: 2个或更多GPU可并行处理

### 流媒体支持
- FFmpeg (用于RTMP流)
- 网络摄像头或流媒体服务器

##  安装

### 1. 安装基础依赖
```bash
pip install -r requirements.txt
```

### 2. GPU支持 (可选但推荐)

#### NVIDIA GPU (CUDA)
```bash
# 卸载CPU版本的PyTorch
pip uninstall torch torchvision

# 安装CUDA版本 (根据你的CUDA版本选择)
pip install torch==2.1.1+cu118 torchvision==0.16.1+cu118 --index-url https://download.pytorch.org/whl/cu118
```

#### Apple Silicon (MPS)
```bash
# MPS支持已包含在标准PyTorch安装中
# 确保你使用的是最新版本的PyTorch
```

### 3. FFmpeg (用于RTMP支持)
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# 下载并安装FFmpeg，确保添加到PATH
```

##   测试GPU功能

运行GPU测试脚本来验证你的设置：

```bash
python gpu_test.py
```

这个脚本会：
- 检测可用的GPU设备
- 测试YOLOv11模型性能
- 显示推荐的配置设置
- 验证环境完整性

##   快速开始

### 1. 启动服务
```bash
cd src
python -m app.main
```

服务将在 http://localhost:2000 启动

### 2. 检查系统状态
```bash
curl http://localhost:2000/api/v1/realtime-ai/gpu-info
```

### 3. 启动RTSP流检测

#### 单GPU模式
```bash
curl -X POST "http://localhost:2000/api/v1/realtime-ai/start-rtsp" \
  -H "Content-Type: application/json" \
  -d '{
    "rtsp_url": "rtsp://your-camera-ip:554/stream",
    "model_variant": "yolov11n",
    "confidence_threshold": 0.5,
    "device": "cuda"
  }'
```

#### 多GPU模式 (如果有多个GPU)
```bash
curl -X POST "http://localhost:2000/api/v1/realtime-ai/start" \
  -H "Content-Type: application/json" \
  -d '{
    "stream_config": {
      "url": "rtsp://your-camera-ip:554/stream",
      "protocol": "rtsp"
    },
    "model_settings": {
      "variant": "multi_gpu_yolov11s",
      "device": "auto",
      "enable_multi_gpu": true,
      "load_balancing": true
    }
  }'
```

### 4. 获取检测结果
```bash
# 获取最新结果
curl http://localhost:2000/api/v1/realtime-ai/results/{service_id}

# 实时流 (Server-Sent Events)
curl http://localhost:2000/api/v1/realtime-ai/results/{service_id}/stream
```

##  API 接口

### 核心端点

#### 启动检测服务
```http
POST /api/v1/realtime-ai/start
```

#### 停止检测服务
```http
POST /api/v1/realtime-ai/stop/{service_id}
```

#### 获取服务状态
```http
GET /api/v1/realtime-ai/status/{service_id}
```

#### 获取检测结果
```http
GET /api/v1/realtime-ai/results/{service_id}
```

#### 实时结果流
```http
GET /api/v1/realtime-ai/results/{service_id}/stream
```

### 系统信息端点

#### GPU信息 (包含多GPU检测)
```http
GET /api/v1/realtime-ai/gpu-info
```

#### 系统信息
```http
GET /api/v1/realtime-ai/system-info
```

#### 健康检查
```http
GET /api/v1/realtime-ai/health
```

### 便捷端点

#### RTSP快速启动
```http
POST /api/v1/realtime-ai/start-rtsp rtsp_url=rtsp://example.com/stream&device=cuda
```

#### RTMP快速启动
```http
POST /api/v1/realtime-ai/start-rtmp rtmp_url=rtmp://example.com/stream&device=cuda
```

##   配置参数

### 检测器配置

#### 单GPU配置
```json
{
  "variant": "yolov11n",           // 模型变体: yolov11n/s/m/l/x
  "confidence_threshold": 0.5,     // 置信度阈值
  "iou_threshold": 0.45,          // IoU阈值
  "device": "cuda",               // 设备: cuda/mps/cpu
  "max_detections": 300,          // 最大检测数量
  "half_precision": true          // 半精度推理 (GPU)
}
```

#### 多GPU配置
```json
{
  "variant": "multi_gpu_yolov11s", // 多GPU模型变体
  "confidence_threshold": 0.5,
  "device": "auto",               // 自动检测最佳设备
  "enable_multi_gpu": true,       // 启用多GPU
  "load_balancing": true,         // 负载均衡
  "gpu_devices": null,            // null=自动检测所有GPU
  "max_workers": 4                // 并行工作线程数
}
```

### 流配置
```json
{
  "url": "rtsp://camera:554/stream",
  "protocol": "rtsp",             // rtsp/rtmp/http/https/file
  "fps": 30,                      // 目标FPS
  "resolution": [1920, 1080],     // 目标分辨率
  "timeout": 30,                  // 连接超时
  "buffer_size": 1                // 缓冲区大小
}
```

### 处理配置
```json
{
  "max_fps": 30,                  // 最大处理FPS
  "skip_frames": 0,               // 跳帧数量
  "batch_size": 1,                // 批处理大小
  "result_buffer_size": 100       // 结果缓冲区大小
}
```

##  模型选择建议

### 基于GPU内存的推荐

| GPU内存 | 推荐模型 | 批处理大小 | 半精度 |
|---------|----------|------------|--------|
| 12GB+   | yolov11x, yolov11l | 4 |   |
| 8GB     | yolov11l, yolov11m | 3 |   |
| 6GB     | yolov11m, yolov11s | 2 |   |
| 4GB     | yolov11s, yolov11n | 1 |   |
| <4GB    | yolov11n | 1 |   |

### 基于性能需求的推荐

| 应用场景 | 推荐模型 | 设备 | 说明 |
|----------|----------|------|------|
| 实时监控 | yolov11n, yolov11s | CUDA | 高FPS，低延迟 |
| 精确检测 | yolov11l, yolov11x | CUDA | 高精度，可接受延迟 |
| 边缘设备 | yolov11n | CPU/MPS | 资源受限环境 |
| 批处理 | yolov11m, yolov11l | CUDA | 平衡性能和精度 |

##  性能优化

### GPU优化
1. **启用半精度**: `half_precision: true` (CUDA)
2. **选择合适的批处理大小**: 根据GPU内存调整
3. **使用最新的CUDA驱动**: 获得最佳性能
4. **预热模型**: 启动时进行几次推理

### 流优化
1. **最小化缓冲区**: `buffer_size: 1` 减少延迟
2. **跳帧处理**: 在高FPS流中使用 `skip_frames`
3. **适当的FPS限制**: 避免不必要的处理负载
4. **网络优化**: 确保稳定的网络连接

### 内存优化
1. **定期清理GPU缓存**: 自动处理，但可手动调用
2. **限制结果缓冲区**: 避免内存泄漏
3. **及时停止不需要的服务**: 释放资源

##   故障排除

### 常见问题

#### GPU不可用
```
WARNING: CUDA requested but not available, falling back to CPU
```
**解决方案**:
1. 检查NVIDIA驱动是否安装
2. 验证CUDA安装: `nvidia-smi`
3. 重新安装CUDA版本的PyTorch

#### 内存不足
```
RuntimeError: CUDA out of memory
```
**解决方案**:
1. 减少批处理大小
2. 使用更小的模型变体
3. 降低输入图像分辨率
4. 启用半精度推理

#### 流连接失败
```
StreamConnectionException: Failed to connect to RTSP stream
```
**解决方案**:
1. 验证流URL是否正确
2. 检查网络连接
3. 确认摄像头/服务器是否在线
4. 调整超时设置

#### FFmpeg未找到
```
FFmpeg: NOT INSTALLED (required for RTMP streams)
```
**解决方案**:
1. 安装FFmpeg: `sudo apt install ffmpeg`
2. 确保FFmpeg在PATH中
3. 重启应用程序

##   监控和日志

### 性能监控
- GPU内存使用情况
- 推理时间统计
- FPS测量
- 错误率跟踪

### 日志级别
- **INFO**: 正常操作
- **WARNING**: 性能警告
- **ERROR**: 错误情况
- **DEBUG**: 详细调试信息

##   自定义扩展

### 添加自定义检测器
```python
from app.realtime_ai.detectors.custom_detector import CustomDetector

def my_load_model(config):
    # 加载你的模型
    return model

def my_inference(model, frame, config):
    # 执行推理
    return results

config = {
    "load_model_callback": my_load_model,
    "inference_callback": my_inference,
    "model_name": "MyCustomModel"
}

detector = CustomDetector(config)
```

### 添加自定义流提供者
```python
from app.realtime_ai.core.base import BaseStreamProvider

class MyStreamProvider(BaseStreamProvider):
    async def connect(self):
        # 实现连接逻辑
        pass
    
    async def get_frame(self):
        # 实现帧获取逻辑
        pass
```

##   贡献

欢迎提交问题报告和功能请求！

##   许可证

请参考项目根目录的LICENSE文件。

---

**  享受使用实时AI识别模块！**

如有任何问题，请查看文档或提交issue。

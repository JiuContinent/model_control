# 🚗 车辆识别AI模块使用指南

这个专门的车辆识别模块基于YOLOv11，专门针对车辆检测和分类进行了优化。

## 🎯 支持的车辆类型

### 基础车辆类型
- **汽车** (car) - 轿车、SUV、掀背车
- **卡车** (truck) - 轻型卡车、重型卡车
- **公交车** (bus) - 城市公交、长途客车
- **摩托车** (motorcycle) - 摩托车、电动车
- **自行车** (bicycle) - 自行车、电动自行车

### 扩展车辆类型
- **火车** (train)
- **船只** (boat)
- **飞机** (airplane)

## 🚀 快速开始

### 1. 检查车辆AI服务状态
```bash
curl http://localhost:2000/api/v1/vehicle-ai/health
```

### 2. 查看支持的车辆类型
```bash
curl http://localhost:2000/api/v1/vehicle-ai/vehicle-types
```

### 3. 快速启动车辆检测
```bash
curl -X POST "http://localhost:2000/api/v1/vehicle-ai/quick-start" \
  -H "Content-Type: application/json" \
  -d '{
    "stream_url": "rtsp://your-camera:554/stream",
    "vehicle_types": ["car", "truck", "bus"],
    "confidence": 0.6,
    "enable_tracking": true
  }'
```

## 📡 API 接口详解

### 启动车辆检测服务

#### 基础配置
```bash
curl -X POST "http://localhost:2000/api/v1/vehicle-ai/start-detection" \
  -H "Content-Type: application/json" \
  -d '{
    "stream_url": "rtsp://camera-ip:554/stream",
    "detector_type": "vehicle_detector",
    "vehicle_config": {
      "vehicle_types": ["car", "truck", "bus", "motorcycle"],
      "min_vehicle_size": 200,
      "enable_tracking": true,
      "confidence_by_type": {
        "car": 0.5,
        "truck": 0.6,
        "bus": 0.6,
        "motorcycle": 0.4
      }
    },
    "confidence_threshold": 0.5,
    "device": "auto"
  }'
```

#### 高级配置（多车型分类）
```bash
curl -X POST "http://localhost:2000/api/v1/vehicle-ai/start-detection" \
  -H "Content-Type: application/json" \
  -d '{
    "stream_url": "rtsp://camera-ip:554/stream",
    "detector_type": "multi_vehicle_type",
    "vehicle_config": {
      "vehicle_types": ["car", "truck", "bus"],
      "enable_tracking": true,
      "enable_sub_classification": true,
      "track_history_size": 50
    },
    "confidence_threshold": 0.6,
    "device": "cuda"
  }'
```

### 获取车辆统计信息
```bash
curl http://localhost:2000/api/v1/vehicle-ai/statistics/{service_id}
```

### 预设配置模板
```bash
curl http://localhost:2000/api/v1/vehicle-ai/presets
```

## 🎛️ 预设配置详解

### 1. 交通监控模式
```json
{
  "vehicle_types": ["car", "truck", "bus", "motorcycle"],
  "confidence_threshold": 0.6,
  "min_vehicle_size": 200,
  "enable_tracking": true,
  "confidence_by_type": {
    "car": 0.5,
    "truck": 0.6,
    "bus": 0.6,
    "motorcycle": 0.4
  }
}
```
**适用场景**: 城市道路、交叉路口、高速公路

### 2. 停车场监控模式
```json
{
  "vehicle_types": ["car", "motorcycle", "bicycle"],
  "confidence_threshold": 0.7,
  "min_vehicle_size": 500,
  "enable_tracking": false
}
```
**适用场景**: 停车场、车库、停车位监控

### 3. 高速公路监控模式
```json
{
  "vehicle_types": ["car", "truck", "bus"],
  "confidence_threshold": 0.5,
  "enable_tracking": true,
  "enable_sub_classification": true
}
```
**适用场景**: 高速公路、快速路、车流统计

### 4. 综合监控模式
```json
{
  "vehicle_types": ["car", "truck", "bus", "motorcycle", "bicycle", "train", "boat", "airplane"],
  "confidence_threshold": 0.4,
  "enable_tracking": true,
  "enable_sub_classification": true
}
```
**适用场景**: 复合交通枢纽、综合监控

## 🔧 配置参数详解

### 车辆检测配置 (`VehicleDetectionConfig`)

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `vehicle_types` | List[str] | ["car", "truck", "bus", "motorcycle", "bicycle"] | 要检测的车辆类型 |
| `min_vehicle_size` | int | 100 | 最小车辆尺寸（像素面积） |
| `confidence_by_type` | Dict[str, float] | {} | 每种车型的置信度阈值 |
| `enable_tracking` | bool | True | 启用车辆跟踪 |
| `track_history_size` | int | 30 | 跟踪历史记录大小 |
| `enable_sub_classification` | bool | False | 启用子分类（轿车、SUV等） |

### 检测器类型

#### `vehicle_detector`
- 基础车辆检测器
- 专门针对车辆优化
- 支持多种车辆类型
- 内置车辆跟踪

#### `multi_vehicle_type`
- 高级多车型检测器
- 支持子分类（轿车/SUV/掀背车等）
- 自定义车辆类型映射
- 增强的分类规则

## 📊 检测结果格式

### 基础检测结果
```json
{
  "frame_id": 123,
  "timestamp": 1677123456.789,
  "detections": [
    {
      "bbox": {
        "x1": 100, "y1": 200,
        "x2": 300, "y2": 400,
        "width": 200, "height": 200,
        "area": 40000, "center": [200, 300]
      },
      "confidence": 0.85,
      "class_id": 2,
      "class_name": "car",
      "additional_info": {
        "vehicle_type": "car",
        "size_category": "medium",
        "aspect_ratio": 1.0,
        "detection_id": "vehicle_123_0",
        "track_id": 15
      }
    }
  ],
  "total_objects": 1,
  "model_info": {
    "detector_type": "VehicleDetector",
    "vehicle_types_detected": ["car"],
    "vehicle_counts": {"car": 1},
    "tracking_enabled": true,
    "active_tracks": 5
  }
}
```

### 车辆统计信息
```json
{
  "vehicle_statistics": {
    "total_detections": 1523,
    "vehicle_counts_by_type": {
      "car": 1200,
      "truck": 200,
      "bus": 80,
      "motorcycle": 43
    },
    "tracking_enabled": true,
    "active_tracks": 12,
    "tracks_by_type": {
      "car": 8,
      "truck": 3,
      "bus": 1
    }
  }
}
```

## 🎯 使用场景示例

### 1. 交通流量监控
```python
# 启动交通流量监控
import requests

response = requests.post("http://localhost:2000/api/v1/vehicle-ai/quick-start", params={
    "stream_url": "rtsp://traffic-camera:554/stream",
    "vehicle_types": ["car", "truck", "bus"],
    "confidence": 0.6,
    "enable_tracking": True
})

service_id = response.json()["service_id"]

# 定期获取统计信息
while True:
    stats = requests.get(f"http://localhost:2000/api/v1/vehicle-ai/statistics/{service_id}")
    vehicle_counts = stats.json()["vehicle_statistics"]["vehicle_counts_by_type"]
    print(f"车流统计: {vehicle_counts}")
    time.sleep(10)
```

### 2. 停车场监控
```python
# 停车场车辆检测
response = requests.post("http://localhost:2000/api/v1/vehicle-ai/start-detection", json={
    "stream_url": "rtsp://parking-camera:554/stream",
    "detector_type": "vehicle_detector",
    "vehicle_config": {
        "vehicle_types": ["car", "motorcycle"],
        "min_vehicle_size": 500,  # 过滤小目标
        "enable_tracking": False,  # 停车场不需要跟踪
        "confidence_by_type": {
            "car": 0.7,
            "motorcycle": 0.6
        }
    }
})
```

### 3. 高速公路监控
```python
# 高速公路车辆分类
response = requests.post("http://localhost:2000/api/v1/vehicle-ai/start-detection", json={
    "stream_url": "rtsp://highway-camera:554/stream",
    "detector_type": "multi_vehicle_type",
    "vehicle_config": {
        "vehicle_types": ["car", "truck", "bus"],
        "enable_sub_classification": True,  # 启用子分类
        "enable_tracking": True,
        "track_history_size": 100
    },
    "device": "cuda"  # 使用GPU加速
})
```

## 🔧 性能优化建议

### 1. 硬件优化
- **GPU**: 推荐使用CUDA GPU获得更好性能
- **内存**: 至少8GB RAM用于流畅处理
- **网络**: 稳定的网络连接对于RTSP流很重要

### 2. 参数调优
```python
# 高性能配置
config = {
    "confidence_threshold": 0.6,     # 提高置信度减少误检
    "min_vehicle_size": 200,         # 过滤小目标减少计算量
    "enable_tracking": True,         # 跟踪提高检测一致性
    "device": "cuda",                # 使用GPU加速
    "max_fps": 15                    # 适当降低FPS减少计算负载
}

# 精度优先配置
config = {
    "confidence_threshold": 0.4,     # 降低阈值检测更多目标
    "min_vehicle_size": 50,          # 检测小目标
    "enable_sub_classification": True, # 启用详细分类
    "track_history_size": 50,        # 更长的跟踪历史
    "device": "cuda",
    "max_fps": 30
}
```

### 3. 场景优化
- **白天监控**: 使用较低的置信度阈值
- **夜间监控**: 提高置信度阈值，增加最小尺寸
- **雨雪天气**: 启用更强的跟踪，降低帧率
- **高流量场景**: 增加批处理大小，使用GPU

## 🐛 故障排除

### 常见问题

#### 1. 检测精度不高
```python
# 解决方案：调整置信度和类型特定阈值
"confidence_by_type": {
    "car": 0.5,      # 汽车相对容易识别
    "motorcycle": 0.4, # 摩托车可能需要更低阈值
    "truck": 0.6     # 卡车要求更高置信度
}
```

#### 2. 跟踪不稳定
```python
# 解决方案：调整跟踪参数
"enable_tracking": True,
"track_history_size": 50,  # 增加历史记录
"min_vehicle_size": 200    # 过滤抖动的小目标
```

#### 3. 性能不足
```python
# 解决方案：性能优化
"device": "cuda",          # 使用GPU
"max_fps": 15,             # 降低处理帧率
"skip_frames": 1,          # 跳帧处理
"min_vehicle_size": 300    # 过滤小目标
```

## 📈 监控和分析

### 实时监控
```bash
# 获取实时统计
curl http://localhost:2000/api/v1/vehicle-ai/statistics/{service_id}

# 获取服务状态
curl http://localhost:2000/api/v1/realtime-ai/status/{service_id}
```

### 数据分析
- **车流量统计**: 按时间段统计不同车型数量
- **速度估算**: 基于跟踪轨迹计算车辆速度
- **密度分析**: 分析交通密度和拥堵情况
- **异常检测**: 识别异常行为或事件

---

**🎉 享受智能车辆识别带来的便利！**

如有任何问题，请查看API文档：http://localhost:2000/docs

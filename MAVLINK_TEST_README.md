# MAVLink 测试工具使用说明

这个项目提供了多个工具来验证MAVLink数据接收功能。

## 文件说明

### 1. `mavlink_test_client.py` - MAVLink测试客户端
用于发送指定的MAVLink数据包到接收器。

**功能：**
- 发送你提供的模拟数据包
- 支持单次发送、连续发送、单个数据包发送
- 支持自定义hex数据发送

**使用方法：**
```bash
python mavlink_test_client.py
```

**包含的测试数据：**
- AHRS消息 (系统ID=9)
- MISSION_CURRENT消息 (系统ID=9)
- GPS_RAW_INT消息 (系统ID=9, 位置32.050190, 119.068106)
- SCALED_IMU3消息 (系统ID=9)

### 2. `verify_mavlink.py` - MAVLink验证工具
用于检查MAVLink接收器的状态和接收到的数据。

**功能：**
- 显示接收器状态
- 查看最近接收的消息
- 显示活跃会话
- 实时监控数据接收

**使用方法：**
```bash
python verify_mavlink.py
```

### 3. `test_mavlink_integration.py` - 集成测试
同时启动接收器和发送测试数据，进行完整的集成测试。

**功能：**
- 自动启动UDP接收器
- 发送测试数据包
- 显示测试结果
- 支持实时监控

**使用方法：**
```bash
python test_mavlink_integration.py
```

## 测试步骤

### 方法1：使用集成测试（推荐）
1. 运行集成测试脚本：
   ```bash
   python test_mavlink_integration.py
   ```
2. 脚本会自动启动接收器并发送测试数据
3. 查看测试结果和接收到的消息

### 方法2：分步测试
1. 首先启动验证工具：
   ```bash
   python verify_mavlink.py
   ```
2. 选择"实时监控"功能
3. 在另一个终端运行测试客户端：
   ```bash
   python mavlink_test_client.py
   ```
4. 选择发送测试数据
5. 观察验证工具中的实时监控结果

### 方法3：使用现有工具
1. 启动项目的主应用（如果支持MAVLink接收）
2. 运行测试客户端发送数据：
   ```bash
   python mavlink_test_client.py
   ```

## 测试数据说明

测试数据包含以下MAVLink消息：

1. **AHRS消息** (28字节)
   - 系统ID: 9
   - 消息ID: 163 (0xA3)
   - 包含姿态和航向信息

2. **MISSION_CURRENT消息** (1字节)
   - 系统ID: 9
   - 消息ID: 42 (0x2A)
   - 当前任务信息

3. **GPS_RAW_INT消息** (44字节)
   - 系统ID: 9
   - 消息ID: 24 (0x18)
   - GPS位置信息 (32.050190, 119.068106)

4. **SCALED_IMU3消息** (24字节)
   - 系统ID: 9
   - 消息ID: 129 (0x81)
   - IMU传感器数据

## 验证要点

运行测试后，你应该能看到：

1. **接收器状态**：
   - 运行状态为"运行中"
   - 监听端口14550
   - 有接收到的消息

2. **接收到的消息**：
   - 消息ID、系统ID、组件ID正确
   - 数据包长度匹配
   - 时间戳正常

3. **活跃会话**：
   - 客户端地址为127.0.0.1:随机端口
   - 系统ID为9
   - 消息数量正确

## 故障排除

### 如果接收器没有收到数据：
1. 检查端口14550是否被占用
2. 确认防火墙设置
3. 检查网络连接

### 如果数据解析失败：
1. 检查MAVLink数据包格式
2. 确认数据包完整性
3. 查看解析器日志

### 如果应用崩溃：
1. 检查Python依赖是否正确安装
2. 确认项目路径设置正确
3. 查看错误日志

## 端口配置

默认配置：
- UDP接收端口：14550
- 目标地址：127.0.0.1 (localhost)

如需修改端口，请编辑相应的Python文件中的端口配置。

## 依赖要求

确保已安装以下Python包：
- asyncio (Python 3.7+)
- socket (标准库)
- struct (标准库)
- threading (标准库)
- datetime (标准库)

项目依赖请参考 `requirements.txt` 文件。

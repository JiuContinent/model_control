#!/usr/bin/env python3
import socket
import time
import requests
from datetime import datetime

def test_real_mavlink_data():
    print("=" * 70)
    # print("使用真实MAVLink数据测试接收器")
    print("=" * 70)
    
    # 真实的MAVLink数据包（十六进制字符串）
    mavlink_packets = [
        # 第一个数据包：ATTITUDE消息
        "fd1600004f0901c10000d79b803dce39923dc4fdda3b20cd803b000000003f0390b7",
        
        # 第二个数据包：SCALED_PRESSURE消息  
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        
        # 第三个数据包：VFR_HUD消息
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f"
    ]
    
    # 连接到MAVLink接收器
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("? 成功连接到MAVLink接收器 (localhost:5760)")
        
        # 发送真实数据包
        for i, hex_data in enumerate(mavlink_packets):
            # 将十六进制字符串转换为字节
            packet_data = bytes.fromhex(hex_data)
            
            # 发送数据包
            sock.send(packet_data)
            print(f"? 发送MAVLink数据包 {i+1}/3 (长度: {len(packet_data)} 字节)")
            print(f"  数据: {hex_data}")
            
            # 等待一下
            time.sleep(1)
        
        sock.close()
        print("? 真实数据包发送完成")
        
        # 等待处理
        print("等待数据处理...")
        time.sleep(2)
        
        # 检查接收器状态
        try:
            response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
            if response.status_code == 200:
                status = response.json()
                print(f"\n? MAVLink接收器状态:")
                print(f"  - 运行状态: {'运行中' if status['is_running'] else '已停止'}")
                print(f"  - 总消息数: {status['total_messages']}")
                print(f"  - 活跃会话: {status['active_sessions']}")
                
                # 检查MQTT状态
                if 'mqtt_status' in status:
                    mqtt_status = status['mqtt_status']
                    print(f"\n? MQTT转发状态:")
                    print(f"  - MQTT连接: {'已连接' if mqtt_status['is_connected'] else '未连接'}")
                    print(f"  - 已发布消息: {mqtt_status['messages_published']}")
                    print(f"  - 主题: {mqtt_status['topic']}")
            else:
                print("? 无法获取接收器状态")
        except Exception as e:
            print(f"? 检查接收器状态失败: {e}")
        
    except Exception as e:
        print(f"? 测试失败: {e}")

def check_mqtt_status():
    """检查MQTT状态"""
    print("\n" + "=" * 70)
    print("检查MQTT服务状态")
    print("=" * 70)
    
    try:
        # 检查MQTT状态
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        if response.status_code == 200:
            status = response.json()
            print(f"? MQTT服务状态:")
            print(f"  - 运行状态: {'运行中' if status['is_running'] else '已停止'}")
            print(f"  - 连接状态: {'已连接' if status['is_connected'] else '未连接'}")
            print(f"  - 代理地址: {status['broker_host']}:{status['broker_port']}")
            print(f"  - 主题: {status['topic']}")
            print(f"  - 已发布消息: {status['messages_published']}")
            
            if status['last_publish_time']:
                print(f"  - 最后发布时间: {status['last_publish_time']}")
        else:
            print("? 无法获取MQTT状态")
            
    except Exception as e:
        print(f"? MQTT状态检查失败: {e}")

def test_mqtt_connection():
    """测试MQTT连接"""
    print("\n" + "=" * 70)
    print("测试MQTT连接")
    print("=" * 70)
    
    try:
        # 尝试启动MQTT服务
        response = requests.post("http://localhost:8000/api/v1/mqtt/start", 
                               json={
                                   "broker_host": "221.226.33.58",
                                   "broker_port": 1883,
                                   "topic": "/ue/device/mavlink"
                               })
        
        if response.status_code == 200:
            result = response.json()
            print("? MQTT服务启动成功")
            print(f"  - 代理: {result['broker_host']}:{result['broker_port']}")
            print(f"  - 主题: {result['topic']}")
        else:
            print(f"? MQTT服务启动失败: {response.text}")
            
    except Exception as e:
        print(f"? MQTT连接测试失败: {e}")

if __name__ == "__main__":
    # 检查MQTT状态
    check_mqtt_status()
    
    # 测试MQTT连接
    test_mqtt_connection()
    
    # 使用真实数据测试
    test_real_mavlink_data()
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("=" * 70)
    print("测试结果说明:")
    print("1. 如果MAVLink接收器能接收数据，说明TCP接收功能正常")
    print("2. 如果MQTT连接成功，数据会自动转发到MQTT主题: /ue/device/mavlink")
    print("3. 你可以使用MQTT客户端订阅该主题来查看转发的数据")
    print("4. 如果MQTT连接失败，可能是网络问题或MQTT服务器不可达")
    print("=" * 70)


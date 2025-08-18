#!/usr/bin/env python3
"""
测试MAVLink数据转发到MQTT的功能
"""
import socket
import time
import json
from datetime import datetime

def create_mavlink_packet(message_id=0, system_id=1, component_id=1, sequence=0, payload=b''):
    """创建简单的MAVLink v1数据包"""
    # MAVLink v1 包头: FE + 长度 + 序列 + 系统ID + 组件ID + 消息ID
    header = bytes([0xFE, len(payload), sequence, system_id, component_id, message_id])
    
    # 计算校验和
    checksum = 0
    for byte in header[1:] + payload:  # 跳过起始字节
        checksum ^= byte
    
    # 添加校验和
    packet = header + payload + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])
    return packet

def test_mavlink_to_mqtt():
    """测试MAVLink数据转发到MQTT"""
    print("=" * 60)
    print("测试MAVLink数据转发到MQTT功能")
    print("=" * 60)
    
    # 连接到MAVLink接收器
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("? 成功连接到MAVLink接收器 (localhost:5760)")
        
        # 发送测试数据包
        test_payload = json.dumps({
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Test MAVLink packet for MQTT forwarding"
        }).encode()
        
        # 创建多个测试数据包
        for i in range(5):
            packet = create_mavlink_packet(
                message_id=i,
                system_id=1,
                component_id=1,
                sequence=i,
                payload=test_payload
            )
            
            sock.send(packet)
            print(f"? 发送MAVLink数据包 {i+1}/5 (长度: {len(packet)} 字节)")
            time.sleep(0.5)
        
        sock.close()
        print("? 测试数据包发送完成")
        
        # 等待MQTT处理
        print("等待MQTT处理...")
        time.sleep(2)
        
        # 检查MQTT状态
        import requests
        try:
            response = requests.get("http://localhost:8000/api/v1/mqtt/status")
            if response.status_code == 200:
                mqtt_status = response.json()
                print(f"? MQTT状态: 已连接")
                print(f"  - 已发布消息数: {mqtt_status['messages_published']}")
                print(f"  - 最后发布时间: {mqtt_status['last_publish_time']}")
                print(f"  - 主题: {mqtt_status['topic']}")
            else:
                print("? 无法获取MQTT状态")
        except Exception as e:
            print(f"? 检查MQTT状态失败: {e}")
        
    except Exception as e:
        print(f"? 测试失败: {e}")

def test_mqtt_connection():
    """测试MQTT连接"""
    print("\n" + "=" * 60)
    print("测试MQTT连接")
    print("=" * 60)
    
    import requests
    
    try:
        # 检查MQTT健康状态
        response = requests.get("http://localhost:8000/api/v1/mqtt/health")
        if response.status_code == 200:
            health = response.json()
            print(f"? MQTT健康状态: {health['status']}")
            print(f"  - 连接状态: {'已连接' if health['mqtt_connected'] else '未连接'}")
            print(f"  - 代理地址: {health['broker_host']}")
            print(f"  - 主题: {health['topic']}")
            print(f"  - 已发布消息: {health['messages_published']}")
        else:
            print("? 无法获取MQTT健康状态")
            
    except Exception as e:
        print(f"? MQTT连接测试失败: {e}")

if __name__ == "__main__":
    # 测试MQTT连接
    test_mqtt_connection()
    
    # 测试MAVLink数据转发
    test_mavlink_to_mqtt()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("现在你可以:")
    print("1. 使用MQTT客户端订阅主题: /ue/device/mavlink")
    print("2. 发送MAVLink数据到 localhost:5760")
    print("3. 查看MQTT中的转发数据")
    print("=" * 60)

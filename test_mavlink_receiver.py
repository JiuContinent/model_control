#!/usr/bin/env python3
"""
测试MAVLink接收器功能
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

def test_mavlink_receiver():
    """测试MAVLink接收器"""
    print("=" * 60)
    print("测试MAVLink接收器功能")
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
            "message": "Test MAVLink packet"
        }).encode()
        
        # 创建多个测试数据包
        for i in range(3):
            packet = create_mavlink_packet(
                message_id=i,
                system_id=1,
                component_id=1,
                sequence=i,
                payload=test_payload
            )
            
            sock.send(packet)
            print(f"? 发送MAVLink数据包 {i+1}/3 (长度: {len(packet)} 字节)")
            time.sleep(0.5)
        
        sock.close()
        print("? 测试数据包发送完成")
        
        # 检查接收器状态
        import requests
        try:
            response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
            if response.status_code == 200:
                status = response.json()
                print(f"? MAVLink接收器状态:")
                print(f"  - 运行状态: {'运行中' if status['is_running'] else '已停止'}")
                print(f"  - 总消息数: {status['total_messages']}")
                print(f"  - 活跃会话: {status['active_sessions']}")
            else:
                print("? 无法获取接收器状态")
        except Exception as e:
            print(f"? 检查接收器状态失败: {e}")
        
    except Exception as e:
        print(f"? 测试失败: {e}")

def test_mqtt_status():
    """测试MQTT状态"""
    print("\n" + "=" * 60)
    print("测试MQTT状态")
    print("=" * 60)
    
    import requests
    
    try:
        # 检查MQTT状态
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        if response.status_code == 200:
            status = response.json()
            print(f"? MQTT状态:")
            print(f"  - 运行状态: {'运行中' if status['is_running'] else '已停止'}")
            print(f"  - 连接状态: {'已连接' if status['is_connected'] else '未连接'}")
            print(f"  - 代理地址: {status['broker_host']}")
            print(f"  - 主题: {status['topic']}")
            print(f"  - 已发布消息: {status['messages_published']}")
        else:
            print("? 无法获取MQTT状态")
            
    except Exception as e:
        print(f"? MQTT状态检查失败: {e}")

if __name__ == "__main__":
    # 测试MQTT状态
    test_mqtt_status()
    
    # 测试MAVLink接收器
    test_mavlink_receiver()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("现在你可以:")
    print("1. 发送MAVLink数据到 localhost:5760")
    print("2. 查看接收器状态")
    print("3. 如果MQTT连接成功，数据会自动转发到MQTT")
    print("=" * 60)

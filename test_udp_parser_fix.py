#!/usr/bin/env python3
"""
测试UDP解析器修复
"""
import asyncio
import socket
import time
from datetime import datetime

async def test_udp_parser():
    """测试UDP解析器"""
    print("=" * 70)
    print("测试UDP MAVLink解析器修复")
    print("=" * 70)
    
    # 真实的MAVLink数据包（十六进制字符串）
    mavlink_packets = [
        # ATTITUDE消息
        "fd1c0000a009011e00006d453d00008b5939a25e743d284441c0ead115bebd954cbd864789bcf113",
        
        # SCALED_PRESSURE消息
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        
        # VFR_HUD消息
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f",
        
        # SYSTEM_TIME消息
        "fd0b0000c809010200007ac33ca2a03c060075473dab22",
        
        # MEMINFO消息
        "fd070000d209019800000000ffffd81a03c244",
        
        # RAW_IMU消息
        "fd1d0000e609011b0000bcc366ef00000000410030001cfc0400e5ff1100ecfe1500700100e313d4a0",
        
        # VIBRATION消息
        "fd140000f00901f10000511367ef00000000916b333d95717c3dc0ad693dcf76",
        
        # MISSION_CURRENT消息
        "fd010000fa09012a0000003473",
        
        # SCALED_IMU2消息
        "fd1800000409017400005d4b3d0046001d0019fcfbff09000400f1fed2ff7401ff13a39d",
        
        # BATTERY_STATUS消息
        "fd2900000e0901930000ffffffffffffffffff7f345affffffffffffffffffffffffffffffffffffffff000000ff000000000189ec",
        
        # SYS_STATUS消息
        "fd1f00001809010100003ffc61132f8061022f8070037c00315affff000000000000000000000000ffb35f",
        
        # SERVO_OUTPUT_RAW消息
        "fd210000220901240000e80576efc805dc054c044c04000000000000000000000000000000e803e803e8036f37",
        
        # EKF_STATUS_REPORT消息
        "fd1600002c0901c10000dd61cc3da34f023dfc0f9c3d085d363d000000003f03f722",
        
        # POWER_STATUS消息
        "fd0500003609017d00000c15000001a37e"
    ]
    
    try:
        # 创建UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        print("? 开始发送MAVLink数据包到UDP接收器...")
        
        # 发送真实数据包
        for i, hex_data in enumerate(mavlink_packets):
            # 将十六进制字符串转换为字节
            packet_data = bytes.fromhex(hex_data)
            
            # 发送数据包到UDP接收器
            sock.sendto(packet_data, ('localhost', 14550))
            print(f"? 发送MAVLink数据包 {i+1}/{len(mavlink_packets)} (长度: {len(packet_data)} 字节)")
            print(f"  数据: {hex_data}")
            
            # 等待一下
            time.sleep(0.1)
        
        sock.close()
        print("? 数据包发送完成")
        
        # 等待处理
        print("等待数据处理...")
        time.sleep(2)
        
        print("\n" + "=" * 70)
        print("测试完成！")
        print("=" * 70)
        print("如果修复成功，您应该看到类似以下的输出：")
        print("[17:47:54.857] 接收到 28 字节的UDP数据 (采样率: 1/10):")
        print("  原始数据 (hex): fd1c0000a009011e00006d453d00008b5939a25e743d284441c0ead115bebd954cbd864789bcf113")
        print("  解析到MAVLink消息: 系统ID=9, 类型=ATTITUDE")
        print("    装备-9: 位置(0.000000, 0.000000) 高度0.0m 电量100%")
        print("=" * 70)
        
    except Exception as e:
        print(f"? 测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_udp_parser())


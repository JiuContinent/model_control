#!/usr/bin/env python3
"""
����UDP�������޸�
"""
import asyncio
import socket
import time
from datetime import datetime

async def test_udp_parser():
    """����UDP������"""
    print("=" * 70)
    print("����UDP MAVLink�������޸�")
    print("=" * 70)
    
    # ��ʵ��MAVLink���ݰ���ʮ�������ַ�����
    mavlink_packets = [
        # ATTITUDE��Ϣ
        "fd1c0000a009011e00006d453d00008b5939a25e743d284441c0ead115bebd954cbd864789bcf113",
        
        # SCALED_PRESSURE��Ϣ
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        
        # VFR_HUD��Ϣ
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f",
        
        # SYSTEM_TIME��Ϣ
        "fd0b0000c809010200007ac33ca2a03c060075473dab22",
        
        # MEMINFO��Ϣ
        "fd070000d209019800000000ffffd81a03c244",
        
        # RAW_IMU��Ϣ
        "fd1d0000e609011b0000bcc366ef00000000410030001cfc0400e5ff1100ecfe1500700100e313d4a0",
        
        # VIBRATION��Ϣ
        "fd140000f00901f10000511367ef00000000916b333d95717c3dc0ad693dcf76",
        
        # MISSION_CURRENT��Ϣ
        "fd010000fa09012a0000003473",
        
        # SCALED_IMU2��Ϣ
        "fd1800000409017400005d4b3d0046001d0019fcfbff09000400f1fed2ff7401ff13a39d",
        
        # BATTERY_STATUS��Ϣ
        "fd2900000e0901930000ffffffffffffffffff7f345affffffffffffffffffffffffffffffffffffffff000000ff000000000189ec",
        
        # SYS_STATUS��Ϣ
        "fd1f00001809010100003ffc61132f8061022f8070037c00315affff000000000000000000000000ffb35f",
        
        # SERVO_OUTPUT_RAW��Ϣ
        "fd210000220901240000e80576efc805dc054c044c04000000000000000000000000000000e803e803e8036f37",
        
        # EKF_STATUS_REPORT��Ϣ
        "fd1600002c0901c10000dd61cc3da34f023dfc0f9c3d085d363d000000003f03f722",
        
        # POWER_STATUS��Ϣ
        "fd0500003609017d00000c15000001a37e"
    ]
    
    try:
        # ����UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        
        print("? ��ʼ����MAVLink���ݰ���UDP������...")
        
        # ������ʵ���ݰ�
        for i, hex_data in enumerate(mavlink_packets):
            # ��ʮ�������ַ���ת��Ϊ�ֽ�
            packet_data = bytes.fromhex(hex_data)
            
            # �������ݰ���UDP������
            sock.sendto(packet_data, ('localhost', 14550))
            print(f"? ����MAVLink���ݰ� {i+1}/{len(mavlink_packets)} (����: {len(packet_data)} �ֽ�)")
            print(f"  ����: {hex_data}")
            
            # �ȴ�һ��
            time.sleep(0.1)
        
        sock.close()
        print("? ���ݰ��������")
        
        # �ȴ�����
        print("�ȴ����ݴ���...")
        time.sleep(2)
        
        print("\n" + "=" * 70)
        print("������ɣ�")
        print("=" * 70)
        print("����޸��ɹ�����Ӧ�ÿ����������µ������")
        print("[17:47:54.857] ���յ� 28 �ֽڵ�UDP���� (������: 1/10):")
        print("  ԭʼ���� (hex): fd1c0000a009011e00006d453d00008b5939a25e743d284441c0ead115bebd954cbd864789bcf113")
        print("  ������MAVLink��Ϣ: ϵͳID=9, ����=ATTITUDE")
        print("    װ��-9: λ��(0.000000, 0.000000) �߶�0.0m ����100%")
        print("=" * 70)
        
    except Exception as e:
        print(f"? ����ʧ��: {e}")

if __name__ == "__main__":
    asyncio.run(test_udp_parser())


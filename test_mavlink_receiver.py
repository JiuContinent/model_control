#!/usr/bin/env python3
"""
����MAVLink����������
"""
import socket
import time
import json
from datetime import datetime

def create_mavlink_packet(message_id=0, system_id=1, component_id=1, sequence=0, payload=b''):
    """�����򵥵�MAVLink v1���ݰ�"""
    # MAVLink v1 ��ͷ: FE + ���� + ���� + ϵͳID + ���ID + ��ϢID
    header = bytes([0xFE, len(payload), sequence, system_id, component_id, message_id])
    
    # ����У���
    checksum = 0
    for byte in header[1:] + payload:  # ������ʼ�ֽ�
        checksum ^= byte
    
    # ���У���
    packet = header + payload + bytes([checksum & 0xFF, (checksum >> 8) & 0xFF])
    return packet

def test_mavlink_receiver():
    """����MAVLink������"""
    print("=" * 60)
    print("����MAVLink����������")
    print("=" * 60)
    
    # ���ӵ�MAVLink������
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("? �ɹ����ӵ�MAVLink������ (localhost:5760)")
        
        # ���Ͳ������ݰ�
        test_payload = json.dumps({
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Test MAVLink packet"
        }).encode()
        
        # ��������������ݰ�
        for i in range(3):
            packet = create_mavlink_packet(
                message_id=i,
                system_id=1,
                component_id=1,
                sequence=i,
                payload=test_payload
            )
            
            sock.send(packet)
            print(f"? ����MAVLink���ݰ� {i+1}/3 (����: {len(packet)} �ֽ�)")
            time.sleep(0.5)
        
        sock.close()
        print("? �������ݰ��������")
        
        # ��������״̬
        import requests
        try:
            response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
            if response.status_code == 200:
                status = response.json()
                print(f"? MAVLink������״̬:")
                print(f"  - ����״̬: {'������' if status['is_running'] else '��ֹͣ'}")
                print(f"  - ����Ϣ��: {status['total_messages']}")
                print(f"  - ��Ծ�Ự: {status['active_sessions']}")
            else:
                print("? �޷���ȡ������״̬")
        except Exception as e:
            print(f"? ��������״̬ʧ��: {e}")
        
    except Exception as e:
        print(f"? ����ʧ��: {e}")

def test_mqtt_status():
    """����MQTT״̬"""
    print("\n" + "=" * 60)
    print("����MQTT״̬")
    print("=" * 60)
    
    import requests
    
    try:
        # ���MQTT״̬
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        if response.status_code == 200:
            status = response.json()
            print(f"? MQTT״̬:")
            print(f"  - ����״̬: {'������' if status['is_running'] else '��ֹͣ'}")
            print(f"  - ����״̬: {'������' if status['is_connected'] else 'δ����'}")
            print(f"  - �����ַ: {status['broker_host']}")
            print(f"  - ����: {status['topic']}")
            print(f"  - �ѷ�����Ϣ: {status['messages_published']}")
        else:
            print("? �޷���ȡMQTT״̬")
            
    except Exception as e:
        print(f"? MQTT״̬���ʧ��: {e}")

if __name__ == "__main__":
    # ����MQTT״̬
    test_mqtt_status()
    
    # ����MAVLink������
    test_mavlink_receiver()
    
    print("\n" + "=" * 60)
    print("������ɣ�")
    print("=" * 60)
    print("���������:")
    print("1. ����MAVLink���ݵ� localhost:5760")
    print("2. �鿴������״̬")
    print("3. ���MQTT���ӳɹ������ݻ��Զ�ת����MQTT")
    print("=" * 60)

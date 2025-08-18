#!/usr/bin/env python3
"""
����MAVLink����ת����MQTT�Ĺ���
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

def test_mavlink_to_mqtt():
    """����MAVLink����ת����MQTT"""
    print("=" * 60)
    print("����MAVLink����ת����MQTT����")
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
            "message": "Test MAVLink packet for MQTT forwarding"
        }).encode()
        
        # ��������������ݰ�
        for i in range(5):
            packet = create_mavlink_packet(
                message_id=i,
                system_id=1,
                component_id=1,
                sequence=i,
                payload=test_payload
            )
            
            sock.send(packet)
            print(f"? ����MAVLink���ݰ� {i+1}/5 (����: {len(packet)} �ֽ�)")
            time.sleep(0.5)
        
        sock.close()
        print("? �������ݰ��������")
        
        # �ȴ�MQTT����
        print("�ȴ�MQTT����...")
        time.sleep(2)
        
        # ���MQTT״̬
        import requests
        try:
            response = requests.get("http://localhost:8000/api/v1/mqtt/status")
            if response.status_code == 200:
                mqtt_status = response.json()
                print(f"? MQTT״̬: ������")
                print(f"  - �ѷ�����Ϣ��: {mqtt_status['messages_published']}")
                print(f"  - ��󷢲�ʱ��: {mqtt_status['last_publish_time']}")
                print(f"  - ����: {mqtt_status['topic']}")
            else:
                print("? �޷���ȡMQTT״̬")
        except Exception as e:
            print(f"? ���MQTT״̬ʧ��: {e}")
        
    except Exception as e:
        print(f"? ����ʧ��: {e}")

def test_mqtt_connection():
    """����MQTT����"""
    print("\n" + "=" * 60)
    print("����MQTT����")
    print("=" * 60)
    
    import requests
    
    try:
        # ���MQTT����״̬
        response = requests.get("http://localhost:8000/api/v1/mqtt/health")
        if response.status_code == 200:
            health = response.json()
            print(f"? MQTT����״̬: {health['status']}")
            print(f"  - ����״̬: {'������' if health['mqtt_connected'] else 'δ����'}")
            print(f"  - �����ַ: {health['broker_host']}")
            print(f"  - ����: {health['topic']}")
            print(f"  - �ѷ�����Ϣ: {health['messages_published']}")
        else:
            print("? �޷���ȡMQTT����״̬")
            
    except Exception as e:
        print(f"? MQTT���Ӳ���ʧ��: {e}")

if __name__ == "__main__":
    # ����MQTT����
    test_mqtt_connection()
    
    # ����MAVLink����ת��
    test_mavlink_to_mqtt()
    
    print("\n" + "=" * 60)
    print("������ɣ�")
    print("=" * 60)
    print("���������:")
    print("1. ʹ��MQTT�ͻ��˶�������: /ue/device/mavlink")
    print("2. ����MAVLink���ݵ� localhost:5760")
    print("3. �鿴MQTT�е�ת������")
    print("=" * 60)

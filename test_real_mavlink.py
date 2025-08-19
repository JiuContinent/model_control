#!/usr/bin/env python3
import socket
import time
import requests
from datetime import datetime

def test_real_mavlink_data():
    print("=" * 70)
    # print("ʹ����ʵMAVLink���ݲ��Խ�����")
    print("=" * 70)
    
    # ��ʵ��MAVLink���ݰ���ʮ�������ַ�����
    mavlink_packets = [
        # ��һ�����ݰ���ATTITUDE��Ϣ
        "fd1600004f0901c10000d79b803dce39923dc4fdda3b20cd803b000000003f0390b7",
        
        # �ڶ������ݰ���SCALED_PRESSURE��Ϣ  
        "fd0e0000aa09011d000081453d007e147b4400000000dd120315",
        
        # ���������ݰ���VFR_HUD��Ϣ
        "fd110000b409014a00006b5f783dbc2d0a3f66666a42c9e5d53cbbd41f"
    ]
    
    # ���ӵ�MAVLink������
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect(('localhost', 5760))
        print("? �ɹ����ӵ�MAVLink������ (localhost:5760)")
        
        # ������ʵ���ݰ�
        for i, hex_data in enumerate(mavlink_packets):
            # ��ʮ�������ַ���ת��Ϊ�ֽ�
            packet_data = bytes.fromhex(hex_data)
            
            # �������ݰ�
            sock.send(packet_data)
            print(f"? ����MAVLink���ݰ� {i+1}/3 (����: {len(packet_data)} �ֽ�)")
            print(f"  ����: {hex_data}")
            
            # �ȴ�һ��
            time.sleep(1)
        
        sock.close()
        print("? ��ʵ���ݰ��������")
        
        # �ȴ�����
        print("�ȴ����ݴ���...")
        time.sleep(2)
        
        # ��������״̬
        try:
            response = requests.get("http://localhost:8000/api/v1/mavlink/receiver/status")
            if response.status_code == 200:
                status = response.json()
                print(f"\n? MAVLink������״̬:")
                print(f"  - ����״̬: {'������' if status['is_running'] else '��ֹͣ'}")
                print(f"  - ����Ϣ��: {status['total_messages']}")
                print(f"  - ��Ծ�Ự: {status['active_sessions']}")
                
                # ���MQTT״̬
                if 'mqtt_status' in status:
                    mqtt_status = status['mqtt_status']
                    print(f"\n? MQTTת��״̬:")
                    print(f"  - MQTT����: {'������' if mqtt_status['is_connected'] else 'δ����'}")
                    print(f"  - �ѷ�����Ϣ: {mqtt_status['messages_published']}")
                    print(f"  - ����: {mqtt_status['topic']}")
            else:
                print("? �޷���ȡ������״̬")
        except Exception as e:
            print(f"? ��������״̬ʧ��: {e}")
        
    except Exception as e:
        print(f"? ����ʧ��: {e}")

def check_mqtt_status():
    """���MQTT״̬"""
    print("\n" + "=" * 70)
    print("���MQTT����״̬")
    print("=" * 70)
    
    try:
        # ���MQTT״̬
        response = requests.get("http://localhost:8000/api/v1/mqtt/status")
        if response.status_code == 200:
            status = response.json()
            print(f"? MQTT����״̬:")
            print(f"  - ����״̬: {'������' if status['is_running'] else '��ֹͣ'}")
            print(f"  - ����״̬: {'������' if status['is_connected'] else 'δ����'}")
            print(f"  - �����ַ: {status['broker_host']}:{status['broker_port']}")
            print(f"  - ����: {status['topic']}")
            print(f"  - �ѷ�����Ϣ: {status['messages_published']}")
            
            if status['last_publish_time']:
                print(f"  - ��󷢲�ʱ��: {status['last_publish_time']}")
        else:
            print("? �޷���ȡMQTT״̬")
            
    except Exception as e:
        print(f"? MQTT״̬���ʧ��: {e}")

def test_mqtt_connection():
    """����MQTT����"""
    print("\n" + "=" * 70)
    print("����MQTT����")
    print("=" * 70)
    
    try:
        # ��������MQTT����
        response = requests.post("http://localhost:8000/api/v1/mqtt/start", 
                               json={
                                   "broker_host": "221.226.33.58",
                                   "broker_port": 1883,
                                   "topic": "/ue/device/mavlink"
                               })
        
        if response.status_code == 200:
            result = response.json()
            print("? MQTT���������ɹ�")
            print(f"  - ����: {result['broker_host']}:{result['broker_port']}")
            print(f"  - ����: {result['topic']}")
        else:
            print(f"? MQTT��������ʧ��: {response.text}")
            
    except Exception as e:
        print(f"? MQTT���Ӳ���ʧ��: {e}")

if __name__ == "__main__":
    # ���MQTT״̬
    check_mqtt_status()
    
    # ����MQTT����
    test_mqtt_connection()
    
    # ʹ����ʵ���ݲ���
    test_real_mavlink_data()
    
    print("\n" + "=" * 70)
    print("������ɣ�")
    print("=" * 70)
    print("���Խ��˵��:")
    print("1. ���MAVLink�������ܽ������ݣ�˵��TCP���չ�������")
    print("2. ���MQTT���ӳɹ������ݻ��Զ�ת����MQTT����: /ue/device/mavlink")
    print("3. �����ʹ��MQTT�ͻ��˶��ĸ��������鿴ת��������")
    print("4. ���MQTT����ʧ�ܣ����������������MQTT���������ɴ�")
    print("=" * 70)


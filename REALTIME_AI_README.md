# ʵʱAIʶ��ģ�� (Real-time AI Recognition Module)

����һ���ִ�����ʵʱAIʶ��ϵͳ��֧�ֶ�����ý��Э�飨RTSP/RTMP����YOLOv11ģ�ͱ��塣

##  ��������

- **������ý��Э��֧��**: RTSP��RTMP��HTTP/HTTPS�������ļ�
- **YOLOv11ģ��ϵ��**: ֧�ִ�nano��extra-large�����б���
- **GPU����**: �Զ����CUDA/MPS��֧�ְ뾫������
- **��GPU���д���**: �Զ����ؾ��⣬֧��2-8��GPUͬʱ����
- **�첽����**: �������첽�ܹ���֧�ֲ���������
- **RESTful API**: ������REST API�ӿ�
- **ʵʱ�����**: Server-Sent Eventsʵʱ���ͼ����
- **����չ�ܹ�**: ����ģʽ֧���Զ������������ṩ��

##  ϵͳҪ��

### ����Ҫ��
- Python 3.11+
- 8GB+ RAM
- OpenCV 4.8+
- Ultralytics YOLOv11

### GPU���� (�Ƽ�)
- NVIDIA GPU: CUDA 11.8+ ֧��
- Apple Silicon: MPS ֧��
- ����4GB GPU�ڴ�
- **��GPU֧��**: 2�������GPU�ɲ��д���

### ��ý��֧��
- FFmpeg (����RTMP��)
- ��������ͷ����ý�������

##  ��װ

### 1. ��װ��������
```bash
pip install -r requirements.txt
```

### 2. GPU֧�� (��ѡ���Ƽ�)

#### NVIDIA GPU (CUDA)
```bash
# ж��CPU�汾��PyTorch
pip uninstall torch torchvision

# ��װCUDA�汾 (�������CUDA�汾ѡ��)
pip install torch==2.1.1+cu118 torchvision==0.16.1+cu118 --index-url https://download.pytorch.org/whl/cu118
```

#### Apple Silicon (MPS)
```bash
# MPS֧���Ѱ����ڱ�׼PyTorch��װ��
# ȷ����ʹ�õ������°汾��PyTorch
```

### 3. FFmpeg (����RTMP֧��)
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# ���ز���װFFmpeg��ȷ����ӵ�PATH
```

##   ����GPU����

����GPU���Խű�����֤������ã�

```bash
python gpu_test.py
```

����ű��᣺
- �����õ�GPU�豸
- ����YOLOv11ģ������
- ��ʾ�Ƽ�����������
- ��֤����������

##   ���ٿ�ʼ

### 1. ��������
```bash
cd src
python -m app.main
```

������ http://localhost:2000 ����

### 2. ���ϵͳ״̬
```bash
curl http://localhost:2000/api/v1/realtime-ai/gpu-info
```

### 3. ����RTSP�����

#### ��GPUģʽ
```bash
curl -X POST "http://localhost:2000/api/v1/realtime-ai/start-rtsp" \
  -H "Content-Type: application/json" \
  -d '{
    "rtsp_url": "rtsp://your-camera-ip:554/stream",
    "model_variant": "yolov11n",
    "confidence_threshold": 0.5,
    "device": "cuda"
  }'
```

#### ��GPUģʽ (����ж��GPU)
```bash
curl -X POST "http://localhost:2000/api/v1/realtime-ai/start" \
  -H "Content-Type: application/json" \
  -d '{
    "stream_config": {
      "url": "rtsp://your-camera-ip:554/stream",
      "protocol": "rtsp"
    },
    "model_settings": {
      "variant": "multi_gpu_yolov11s",
      "device": "auto",
      "enable_multi_gpu": true,
      "load_balancing": true
    }
  }'
```

### 4. ��ȡ�����
```bash
# ��ȡ���½��
curl http://localhost:2000/api/v1/realtime-ai/results/{service_id}

# ʵʱ�� (Server-Sent Events)
curl http://localhost:2000/api/v1/realtime-ai/results/{service_id}/stream
```

##  API �ӿ�

### ���Ķ˵�

#### ����������
```http
POST /api/v1/realtime-ai/start
```

#### ֹͣ������
```http
POST /api/v1/realtime-ai/stop/{service_id}
```

#### ��ȡ����״̬
```http
GET /api/v1/realtime-ai/status/{service_id}
```

#### ��ȡ�����
```http
GET /api/v1/realtime-ai/results/{service_id}
```

#### ʵʱ�����
```http
GET /api/v1/realtime-ai/results/{service_id}/stream
```

### ϵͳ��Ϣ�˵�

#### GPU��Ϣ (������GPU���)
```http
GET /api/v1/realtime-ai/gpu-info
```

#### ϵͳ��Ϣ
```http
GET /api/v1/realtime-ai/system-info
```

#### �������
```http
GET /api/v1/realtime-ai/health
```

### ��ݶ˵�

#### RTSP��������
```http
POST /api/v1/realtime-ai/start-rtsp rtsp_url=rtsp://example.com/stream&device=cuda
```

#### RTMP��������
```http
POST /api/v1/realtime-ai/start-rtmp rtmp_url=rtmp://example.com/stream&device=cuda
```

##   ���ò���

### ���������

#### ��GPU����
```json
{
  "variant": "yolov11n",           // ģ�ͱ���: yolov11n/s/m/l/x
  "confidence_threshold": 0.5,     // ���Ŷ���ֵ
  "iou_threshold": 0.45,          // IoU��ֵ
  "device": "cuda",               // �豸: cuda/mps/cpu
  "max_detections": 300,          // ���������
  "half_precision": true          // �뾫������ (GPU)
}
```

#### ��GPU����
```json
{
  "variant": "multi_gpu_yolov11s", // ��GPUģ�ͱ���
  "confidence_threshold": 0.5,
  "device": "auto",               // �Զ��������豸
  "enable_multi_gpu": true,       // ���ö�GPU
  "load_balancing": true,         // ���ؾ���
  "gpu_devices": null,            // null=�Զ��������GPU
  "max_workers": 4                // ���й����߳���
}
```

### ������
```json
{
  "url": "rtsp://camera:554/stream",
  "protocol": "rtsp",             // rtsp/rtmp/http/https/file
  "fps": 30,                      // Ŀ��FPS
  "resolution": [1920, 1080],     // Ŀ��ֱ���
  "timeout": 30,                  // ���ӳ�ʱ
  "buffer_size": 1                // ��������С
}
```

### ��������
```json
{
  "max_fps": 30,                  // �����FPS
  "skip_frames": 0,               // ��֡����
  "batch_size": 1,                // �������С
  "result_buffer_size": 100       // �����������С
}
```

##  ģ��ѡ����

### ����GPU�ڴ���Ƽ�

| GPU�ڴ� | �Ƽ�ģ�� | �������С | �뾫�� |
|---------|----------|------------|--------|
| 12GB+   | yolov11x, yolov11l | 4 |   |
| 8GB     | yolov11l, yolov11m | 3 |   |
| 6GB     | yolov11m, yolov11s | 2 |   |
| 4GB     | yolov11s, yolov11n | 1 |   |
| <4GB    | yolov11n | 1 |   |

### ��������������Ƽ�

| Ӧ�ó��� | �Ƽ�ģ�� | �豸 | ˵�� |
|----------|----------|------|------|
| ʵʱ��� | yolov11n, yolov11s | CUDA | ��FPS�����ӳ� |
| ��ȷ��� | yolov11l, yolov11x | CUDA | �߾��ȣ��ɽ����ӳ� |
| ��Ե�豸 | yolov11n | CPU/MPS | ��Դ���޻��� |
| ������ | yolov11m, yolov11l | CUDA | ƽ�����ܺ;��� |

##  �����Ż�

### GPU�Ż�
1. **���ð뾫��**: `half_precision: true` (CUDA)
2. **ѡ����ʵ��������С**: ����GPU�ڴ����
3. **ʹ�����µ�CUDA����**: ����������
4. **Ԥ��ģ��**: ����ʱ���м�������

### ���Ż�
1. **��С��������**: `buffer_size: 1` �����ӳ�
2. **��֡����**: �ڸ�FPS����ʹ�� `skip_frames`
3. **�ʵ���FPS����**: ���ⲻ��Ҫ�Ĵ�����
4. **�����Ż�**: ȷ���ȶ�����������

### �ڴ��Ż�
1. **��������GPU����**: �Զ����������ֶ�����
2. **���ƽ��������**: �����ڴ�й©
3. **��ʱֹͣ����Ҫ�ķ���**: �ͷ���Դ

##   �����ų�

### ��������

#### GPU������
```
WARNING: CUDA requested but not available, falling back to CPU
```
**�������**:
1. ���NVIDIA�����Ƿ�װ
2. ��֤CUDA��װ: `nvidia-smi`
3. ���°�װCUDA�汾��PyTorch

#### �ڴ治��
```
RuntimeError: CUDA out of memory
```
**�������**:
1. �����������С
2. ʹ�ø�С��ģ�ͱ���
3. ��������ͼ��ֱ���
4. ���ð뾫������

#### ������ʧ��
```
StreamConnectionException: Failed to connect to RTSP stream
```
**�������**:
1. ��֤��URL�Ƿ���ȷ
2. �����������
3. ȷ������ͷ/�������Ƿ�����
4. ������ʱ����

#### FFmpegδ�ҵ�
```
FFmpeg: NOT INSTALLED (required for RTMP streams)
```
**�������**:
1. ��װFFmpeg: `sudo apt install ffmpeg`
2. ȷ��FFmpeg��PATH��
3. ����Ӧ�ó���

##   ��غ���־

### ���ܼ��
- GPU�ڴ�ʹ�����
- ����ʱ��ͳ��
- FPS����
- �����ʸ���

### ��־����
- **INFO**: ��������
- **WARNING**: ���ܾ���
- **ERROR**: �������
- **DEBUG**: ��ϸ������Ϣ

##   �Զ�����չ

### ����Զ�������
```python
from app.realtime_ai.detectors.custom_detector import CustomDetector

def my_load_model(config):
    # �������ģ��
    return model

def my_inference(model, frame, config):
    # ִ������
    return results

config = {
    "load_model_callback": my_load_model,
    "inference_callback": my_inference,
    "model_name": "MyCustomModel"
}

detector = CustomDetector(config)
```

### ����Զ������ṩ��
```python
from app.realtime_ai.core.base import BaseStreamProvider

class MyStreamProvider(BaseStreamProvider):
    async def connect(self):
        # ʵ�������߼�
        pass
    
    async def get_frame(self):
        # ʵ��֡��ȡ�߼�
        pass
```

##   ����

��ӭ�ύ���ⱨ��͹�������

##   ���֤

��ο���Ŀ��Ŀ¼��LICENSE�ļ���

---

**  ����ʹ��ʵʱAIʶ��ģ�飡**

�����κ����⣬��鿴�ĵ����ύissue��

"""
AI服务测试
"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.ai_service import AIService


class TestAIService:
    """AI服务测试类"""
    
    @pytest.fixture
    def ai_service(self):
        """创建AI服务实例"""
        with patch('ultralytics.YOLO'):
            service = AIService()
            return service
    
    def test_init(self, ai_service):
        """测试初始化"""
        assert ai_service.model is not None
        assert ai_service.model_config is not None
    
    @pytest.mark.asyncio
    async def test_detect_objects(self, ai_service):
        """测试目标检测"""
        # 模拟检测结果
        mock_result = Mock()
        mock_result.boxes = Mock()
        mock_result.boxes.xyxy = [[100, 100, 200, 200]]
        mock_result.boxes.conf = [0.8]
        mock_result.boxes.cls = [0]
        
        ai_service.model.return_value = [mock_result]
        ai_service.model.names = {0: "person"}
        
        result = await ai_service.detect_objects("test_image.jpg")
        
        assert "detections" in result
        assert "total_objects" in result
        assert result["total_objects"] == 1
    
    def test_get_model_info(self, ai_service):
        """测试获取模型信息"""
        info = ai_service.get_model_info()
        
        assert "model_name" in info
        assert "confidence_threshold" in info
        assert "iou_threshold" in info
        assert info["model_name"] == "YOLOv11"


if __name__ == "__main__":
    pytest.main([__file__])

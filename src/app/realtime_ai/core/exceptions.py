"""
Custom exceptions for real-time AI recognition system.
"""


class RealtimeAIException(Exception):
    """Base exception for real-time AI system"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "REALTIME_AI_ERROR"
        self.details = details or {}


class StreamException(RealtimeAIException):
    """Exception related to stream processing"""
    
    def __init__(self, message: str, stream_url: str = None, **kwargs):
        super().__init__(message, error_code="STREAM_ERROR", **kwargs)
        self.stream_url = stream_url


class StreamConnectionException(StreamException):
    """Exception when unable to connect to stream"""
    
    def __init__(self, message: str, stream_url: str = None, **kwargs):
        super().__init__(message, stream_url, error_code="STREAM_CONNECTION_ERROR", **kwargs)


class StreamTimeoutException(StreamException):
    """Exception when stream operation times out"""
    
    def __init__(self, message: str, stream_url: str = None, timeout: int = None, **kwargs):
        super().__init__(message, stream_url, error_code="STREAM_TIMEOUT_ERROR", **kwargs)
        self.timeout = timeout


class DetectionException(RealtimeAIException):
    """Exception related to AI detection"""
    
    def __init__(self, message: str, model_name: str = None, **kwargs):
        super().__init__(message, error_code="DETECTION_ERROR", **kwargs)
        self.model_name = model_name


class ModelLoadException(DetectionException):
    """Exception when unable to load AI model"""
    
    def __init__(self, message: str, model_path: str = None, **kwargs):
        super().__init__(message, error_code="MODEL_LOAD_ERROR", **kwargs)
        self.model_path = model_path


class ModelInferenceException(DetectionException):
    """Exception during model inference"""
    
    def __init__(self, message: str, frame_id: int = None, **kwargs):
        super().__init__(message, error_code="MODEL_INFERENCE_ERROR", **kwargs)
        self.frame_id = frame_id


class ConfigurationException(RealtimeAIException):
    """Exception related to configuration"""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        self.config_key = config_key

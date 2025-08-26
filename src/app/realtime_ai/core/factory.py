"""
Factory classes for creating detectors and stream providers.

Implements the Factory Pattern for easy instantiation and registration
of different detector and stream provider types.
"""

from typing import Dict, Type, Any, Optional
from .base import (
    BaseRealtimeDetector, 
    BaseStreamProvider, 
    DetectorType, 
    StreamProtocol,
    StreamConfig
)
from .exceptions import ConfigurationException


class DetectorFactory:
    """Factory for creating AI detectors"""
    
    _detectors: Dict[DetectorType, Type[BaseRealtimeDetector]] = {}
    
    @classmethod
    def register(cls, detector_type: DetectorType, detector_class: Type[BaseRealtimeDetector]):
        """Register a new detector type"""
        cls._detectors[detector_type] = detector_class
    
    @classmethod
    def create(cls, detector_type: DetectorType, model_config: Dict[str, Any]) -> BaseRealtimeDetector:
        """Create a detector instance"""
        if detector_type not in cls._detectors:
            available_types = list(cls._detectors.keys())
            raise ConfigurationException(
                f"Detector type '{detector_type}' not registered. "
                f"Available types: {available_types}",
                config_key="detector_type"
            )
        
        detector_class = cls._detectors[detector_type]
        return detector_class(model_config)
    
    @classmethod
    def get_available_types(cls) -> list[DetectorType]:
        """Get list of available detector types"""
        return list(cls._detectors.keys())
    
    @classmethod
    def is_registered(cls, detector_type: DetectorType) -> bool:
        """Check if detector type is registered"""
        return detector_type in cls._detectors


class StreamProviderFactory:
    """Factory for creating stream providers"""
    
    _providers: Dict[StreamProtocol, Type[BaseStreamProvider]] = {}
    
    @classmethod
    def register(cls, protocol: StreamProtocol, provider_class: Type[BaseStreamProvider]):
        """Register a new stream provider"""
        cls._providers[protocol] = provider_class
    
    @classmethod
    def create(cls, config: StreamConfig) -> BaseStreamProvider:
        """Create a stream provider instance"""
        if config.protocol not in cls._providers:
            available_protocols = list(cls._providers.keys())
            raise ConfigurationException(
                f"Stream protocol '{config.protocol}' not supported. "
                f"Available protocols: {available_protocols}",
                config_key="stream_protocol"
            )
        
        provider_class = cls._providers[config.protocol]
        return provider_class(config)
    
    @classmethod
    def create_from_url(cls, url: str, **kwargs) -> BaseStreamProvider:
        """Create stream provider from URL (auto-detect protocol)"""
        protocol = cls._detect_protocol_from_url(url)
        config = StreamConfig(url=url, protocol=protocol, **kwargs)
        return cls.create(config)
    
    @classmethod
    def _detect_protocol_from_url(cls, url: str) -> StreamProtocol:
        """Auto-detect protocol from URL"""
        url_lower = url.lower()
        
        if url_lower.startswith('rtsp://'):
            return StreamProtocol.RTSP
        elif url_lower.startswith('rtmp://'):
            return StreamProtocol.RTMP
        elif url_lower.startswith('http://'):
            return StreamProtocol.HTTP
        elif url_lower.startswith('https://'):
            return StreamProtocol.HTTPS
        elif url_lower.startswith('file://') or '/' in url or '\\' in url:
            return StreamProtocol.FILE
        else:
            raise ConfigurationException(
                f"Unable to detect protocol from URL: {url}",
                config_key="stream_url"
            )
    
    @classmethod
    def get_available_protocols(cls) -> list[StreamProtocol]:
        """Get list of available protocols"""
        return list(cls._providers.keys())
    
    @classmethod
    def is_supported(cls, protocol: StreamProtocol) -> bool:
        """Check if protocol is supported"""
        return protocol in cls._providers


# Convenience function for creating complete systems
def create_realtime_ai_system(
    detector_type: DetectorType,
    model_config: Dict[str, Any],
    stream_config: StreamConfig
) -> tuple[BaseRealtimeDetector, BaseStreamProvider]:
    """
    Create a complete real-time AI system
    
    Returns:
        Tuple of (detector, stream_provider)
    """
    detector = DetectorFactory.create(detector_type, model_config)
    stream_provider = StreamProviderFactory.create(stream_config)
    
    return detector, stream_provider


def create_system_from_url(
    detector_type: DetectorType,
    model_config: Dict[str, Any],
    stream_url: str,
    **stream_kwargs
) -> tuple[BaseRealtimeDetector, BaseStreamProvider]:
    """
    Create system from stream URL (auto-detect protocol)
    
    Returns:
        Tuple of (detector, stream_provider)
    """
    detector = DetectorFactory.create(detector_type, model_config)
    stream_provider = StreamProviderFactory.create_from_url(stream_url, **stream_kwargs)
    
    return detector, stream_provider

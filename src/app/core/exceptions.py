"""
Custom exception classes
"""


class ModelControlException(Exception):
    """Base exception class"""
    pass


class AIProcessingException(ModelControlException):
    """AI processing exception"""
    pass


class MAVLinkException(ModelControlException):
    """MAVLink related exception"""
    pass


class DatabaseException(ModelControlException):
    """Database exception"""
    pass


class ConfigurationException(ModelControlException):
    """Configuration exception"""
    pass


class ValidationException(ModelControlException):
    """Data validation exception"""
    pass

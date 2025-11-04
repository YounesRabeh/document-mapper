from enum import Enum

class LogLevel(Enum):
    """Logging level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ThemeMode(Enum):
    """Theme mode enumeration"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
from datetime import datetime
from core.enums.log_level import LogLevel


class Logger:
    """Simple custom logger with colored output based on log level."""

    # ANSI color codes (works in most terminals)
    COLORS = {
        LogLevel.DEBUG: "\033[95m",     # Purple
        LogLevel.INFO: "\033[94m",      # Blue
        LogLevel.WARNING: "\033[93m",   # Yellow
        LogLevel.ERROR: "\033[91m",     # Red
        LogLevel.CRITICAL: "\033[41m",  # Red background
    }

    RESET = "\033[0m"

    @staticmethod
    def log(message: str, level: LogLevel = LogLevel.INFO):
        """Logs a message with a colored level tag and timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = Logger.COLORS.get(level, "")
        reset = Logger.RESET
        print(f"{color}[{timestamp}] [{level.value}] {message}{reset}")

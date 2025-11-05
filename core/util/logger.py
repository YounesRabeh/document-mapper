import os
import sys
import platform
from datetime import datetime
from pathlib import Path

from core.enums.log_level import LogLevel


class Logger:
    """
    Custom logger with colored console output and optional file logging.
    Automatically configured from environment variables.
    """

    ENABLE_CONSOLE_OUTPUT: bool = False
    LEVEL: LogLevel = LogLevel.INFO
    LOG_TO_FILE: bool = False
    LOG_FILE_PATH: Path = Path("logs/app.log")
    FORCE_COLORED_OUTPUT: bool = False

    _COLORS = {
        LogLevel.DEBUG: "\033[38;5;213m",    # soft magenta
        LogLevel.INFO: "\033[38;5;39m",      # blue
        LogLevel.WARNING: "\033[38;5;214m",  # orange-yellow
        LogLevel.ERROR: "\033[38;5;196m",    # red
        LogLevel.CRITICAL: "\033[1;41m",     # red background (bold)
    }
    RESET = "\033[0m"



    _PRIORITY = {
        LogLevel.DEBUG: 10,
        LogLevel.INFO: 20,
        LogLevel.WARNING: 30,
        LogLevel.ERROR: 40,
        LogLevel.CRITICAL: 50,
    }

    @classmethod
    def _truthy(cls, val: str) -> bool:
        return str(val).strip().lower() in ("1", "true", "yes", "on")

    # ---------------------------
    # Initialization
    # ---------------------------
    @classmethod
    def configure_from_env(cls):
        """Configure logger behavior from environment variables."""
        cls.ENABLE_CONSOLE_OUTPUT = cls._truthy(os.getenv("ENABLE_CONSOLE_OUTPUT", ""))
        logging = cls._truthy(os.getenv("LOGGING", ""))
        cls.FORCE_COLORED_OUTPUT = cls._truthy(os.getenv("FORCE_COLORED_OUTPUT", ""))

        if logging:
            cls.LEVEL = LogLevel.DEBUG
            cls.LOG_TO_FILE = True
        else:
            log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
            cls.LEVEL = LogLevel.__members__.get(log_level_name, LogLevel.INFO)
            cls.LOG_TO_FILE = False

        # Determine log file path
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        cls.LOG_FILE_PATH = Path(f"logs/app_{timestamp}.log")

        # Auto-create log directory
        if cls.LOG_TO_FILE:
            cls.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            cls._write_file_header()

        # Disable colors if not a TTY and FORCE_COLOR not set

        if not sys.stdout.isatty() and not cls.FORCE_COLORED_OUTPUT:
            cls._COLORS = {level: "" for level in cls._COLORS}
            cls.RESET = ""

        cls.debug("Logger configured successfully.")

    # ---------------------------
    # File Header
    # ---------------------------
    @classmethod
    def _write_file_header(cls):
        """Writes an informative header at the top of the log file."""
        app_name = os.getenv("LOGGING_TARGET_NAME", "Unnamed Application")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header_lines = [
            "=" * 70,
            f"> LOG FILE for {app_name}",
            f"  Session started: {now}",
            "",
            "> CONFIGURATION: ",
            f"   Log Level ........... {cls.LEVEL.name}",
            f"   Forced Colored Output {'Enabled' if cls.FORCE_COLORED_OUTPUT else 'Disabled'}",
            "",
            "> SYSTEM INFO: ",
            f"   Python ............... {sys.version.split()[0]}",
            f"   Platform ............. {platform.system()} {platform.release()}",
            f"   Working Directory .... {Path.cwd()}",
            "=" * 70,
            "",
        ]

        try:
            with open(cls.LOG_FILE_PATH, "w", encoding="utf-8") as f:
                f.write("\n".join(header_lines) + "\n")
        except Exception as e:
            if cls.ENABLE_CONSOLE_OUTPUT:
                print(f"[LoggerError] Failed to write header to log file: {e}")

    # ---------------------------
    # Core Logging
    # ---------------------------
    @classmethod
    def _enabled_for(cls, level: LogLevel) -> bool:
        """Return True if the log level is >= current filter."""
        return cls._PRIORITY.get(level, 0) >= cls._PRIORITY.get(cls.LEVEL, 0)

    @classmethod
    def log(cls, message: str, level: LogLevel = LogLevel.INFO):
        """Logs a message to console and optionally to file."""
        if not cls._enabled_for(level):
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        plain_text = f"[{timestamp}] [{level.name}] {message}"

        # Console output (colored)
        if cls.ENABLE_CONSOLE_OUTPUT:
            color = cls._COLORS.get(level, "")
            reset = cls.RESET if color else ""
            print(f"{color}{plain_text}{reset}")

        # File output (no colors)
        if cls.LOG_TO_FILE:
            try:
                with open(cls.LOG_FILE_PATH, "a", encoding="utf-8") as f:
                    f.write(plain_text + "\n")
            except Exception as e:
                if cls.ENABLE_CONSOLE_OUTPUT:
                    print(f"[LoggerError] Failed to write to log file: {e}")

    # ---------------------------
    # Convenience Shortcuts
    # ---------------------------
    @classmethod
    def debug(cls, msg: str): cls.log(msg, LogLevel.DEBUG)
    @classmethod
    def info(cls, msg: str): cls.log(msg, LogLevel.INFO)
    @classmethod
    def warning(cls, msg: str): cls.log(msg, LogLevel.WARNING)
    @classmethod
    def error(cls, msg: str): cls.log(msg, LogLevel.ERROR)
    @classmethod
    def critical(cls, msg: str): cls.log(msg, LogLevel.CRITICAL)

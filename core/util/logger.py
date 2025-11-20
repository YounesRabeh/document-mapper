import os
import platform
import sys
from datetime import datetime
from pathlib import Path

from core.enums.log_level import LogLevel


class Logger:
    """
    Custom logger with colored console output and optional file logging.
    Automatically configured from environment variables.
    """
    log_file_name: str = "__app.log"

    CONSOLE_OUTPUT_ENABLED: bool = False
    LEVEL: LogLevel = LogLevel.INFO
    PERSISTENCE_LOGGING: bool = False
    LOG_FILE_PATH: Path = Path(log_file_name)
    CONSOLE_FORCE_COLORED: bool = False

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
    def _get_app_root(cls) -> Path:
        """Get the application root directory consistently."""
        if hasattr(sys, "_MEIPASS"):
            # PyInstaller bundle - use the directory where the executable is located
            return Path(sys.executable).parent.resolve()
        else:
            # Normal dev run - use the script's directory
            return Path(__file__).parent.parent.resolve()

    @classmethod
    def _truthy(cls, val: str) -> bool:
        return str(val).strip().lower() in ("1", "true", "yes", "on")

    # ---------------------------
    # Initialization
    # ---------------------------
    @classmethod
    def configure_from_env(cls, project_root:Path = Path.cwd()):
        """Configure logger behavior from environment variables."""
        cls.CONSOLE_OUTPUT_ENABLED = cls._truthy(os.getenv("CONSOLE_OUTPUT_ENABLED", ""))
        logging = cls._truthy(os.getenv("PERSISTENCE_LOGGING", ""))
        cls.CONSOLE_FORCE_COLORED = cls._truthy(os.getenv("CONSOLE_FORCE_COLORED", ""))

        if logging:
            cls.LEVEL = LogLevel.DEBUG
            cls.PERSISTENCE_LOGGING = True
        else:
            log_level_name = os.getenv("CONSOLE_OUTPUT_LEVEL", "INFO").upper()
            cls.LEVEL = LogLevel.__members__.get(log_level_name, LogLevel.INFO)
            cls.PERSISTENCE_LOGGING = False

        # Determine log file path
        cls.LOG_FILE_PATH = (project_root / cls.log_file_name).resolve()

        # Auto-create log directory
        if cls.PERSISTENCE_LOGGING:
            cls.LOG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
            cls._write_file_header()

        # Disable colors if not a TTY and FORCE_COLOR not set
        if not sys.stdout.isatty() and not cls.CONSOLE_FORCE_COLORED:
            cls._COLORS = {level: "" for level in cls._COLORS}
            cls.RESET = ""

        cls.debug("Logger configured successfully.")

    # ---------------------------
    # File Header
    # ---------------------------
    @classmethod
    def _write_file_header(cls):
        """Writes an informative header at the top of the log file."""
        app_name = os.getenv("PERSISTENCE_LOGGING_TARGET_NAME", "Unnamed Application")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        header_lines = [
            "=" * 70,
            f"> LOG FILE for {app_name}",
            f"  Session started: {now}",
            "",
            "> CONFIGURATION: ",
            f"   Log Level ........... {cls.LEVEL.name}",
            f"   Forced Colored Output {'Enabled' if cls.CONSOLE_FORCE_COLORED else 'Disabled'}",
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
            if cls.CONSOLE_OUTPUT_ENABLED:
                Logger.log(f"[LoggerError] Failed to write log file header: {e}", LogLevel.ERROR)

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
        if cls.CONSOLE_OUTPUT_ENABLED:
            color = cls._COLORS.get(level, "")
            reset = cls.RESET if color else ""
            print(f"{color}{plain_text}{reset}")

        # File output (no colors)
        if cls.PERSISTENCE_LOGGING:
            try:
                with open(cls.LOG_FILE_PATH, "a", encoding="utf-8") as f:
                    f.write(plain_text + "\n")
            except Exception as e:
                if cls.CONSOLE_OUTPUT_ENABLED:
                    print(f"!!! - LoggerError: Failed to write to log file: {e}")

    # ---------------------------
    # Convenience Shortcuts
    # ---------------------------

    @classmethod
    def _format_message(cls, msg: str, tag=None) -> str:
        import inspect

        if tag is None:
            # Get caller info two frames up
            frame = inspect.currentframe().f_back.f_back
            caller_self = frame.f_locals.get('self')
            caller_cls = frame.f_locals.get('cls')
            func_name = frame.f_code.co_name  # function name

            if caller_self and hasattr(caller_self, '__class__'):
                tag = caller_self.__class__.__name__
            elif caller_cls and hasattr(caller_cls, '__name__'):
                tag = caller_cls.__name__
            elif func_name and func_name != "<module>":
                tag = func_name
            else:
                module = inspect.getmodule(frame)
                tag = getattr(module, '__name__', '?').split('.')[-1]

            # Clean up weird or useless tags
            if tag in ("str", "builtins", "__main__"):
                tag = "?"
        elif not isinstance(tag, str):
            tag = str(tag)

        return f"[{tag}] {msg}"

    @classmethod
    def debug(cls, msg: str, tag=None):
        """
        Log a debug-level message.


        :param msg: The message to log.
        :param tag: Custom tag to prefix the log message.
                If not provided, the tag defaults to the caller's class name
                or module name.
        """
        cls.log(cls._format_message(msg, tag), LogLevel.DEBUG)

    @classmethod
    def info(cls, msg: str, tag=None):
        """
        Log an informational message.

        :param msg: The message to log.
        :param tag: Custom tag to prefix the log message.
                If not provided, the tag defaults to the caller's class name
                or module name.
        """
        cls.log(cls._format_message(msg, tag), LogLevel.INFO)

    @classmethod
    def warning(cls, msg: str, tag=None):
        """
        Log a warning message.


        :param msg: The message to log.
        :param tag: Custom tag to prefix the log message.
                If not provided, the tag defaults to the caller's class name
                or module name.
        """
        cls.log(cls._format_message(msg, tag), LogLevel.WARNING)

    @classmethod
    def error(cls, msg: str, tag=None):
        """
        Log an error message.


        :param msg: The message to log.
        :param tag: Custom tag to prefix the log message.
                If not provided, the tag defaults to the caller's class name
                or module name.
        """
        cls.log(cls._format_message(msg, tag), LogLevel.ERROR)

    @classmethod
    def critical(cls, msg: str, tag=None):
        """
        Log a critical (highest-severity) message.


        :param msg: The message to log.
        :param tag: Custom tag to prefix the log message.
                If not provided, the tag defaults to the caller's class name
                or module name.
        """
        cls.log(cls._format_message(msg, tag), LogLevel.CRITICAL)

    @classmethod
    def exception(cls, msg: str, tag=None):
        """
        Log an ERROR message including the full traceback of the current exception.
        Should only be used inside an except block.

        :param msg: The message to log.
        :param tag: Custom tag to prefix the log message.
                If not provided, the tag defaults to the caller's class name
                or module name.
        """
        import traceback
        full_msg = f"{msg}\n{traceback.format_exc()}"
        cls.error(full_msg, tag=tag)

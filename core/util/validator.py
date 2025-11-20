from pathlib import Path
from typing import Any

from core.enums.app_themes import AppTheme
from core.enums.log_level import LogLevel

class ConfigValidator:
    """
    Validation and type-conversion utilities for configuration values.

    Provides centralized input validation for configuration values from TOML or
    environment variables. Ensures proper types and consistency before merging
    into the main configuration.
    """

    @staticmethod
    def ensure_positive_int(value: Any, default: int, field_name: str = "value") -> int:
        """
        Ensure the value is a positive integer.

        :param value: Raw input value.
        :param default: Unused; kept for API consistency.
        :param field_name: Name of the field for error messages.
        :returns: Positive integer.
        :raises ValueError: If value is not a positive integer.
        """
        try:
            int_value = int(value)
            if int_value > 0:
                return int_value
            else:
                raise ValueError(f"{field_name} must be positive")
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {field_name}: {value} - {str(e)}") from e

    @staticmethod
    def ensure_boolean(value: Any, default: bool, field_name: str = "value") -> bool:
        """
        Ensure the value represents a boolean.

        :param value: Raw input value.
        :param default: Unused; kept for API consistency.
        :param field_name: Name of the field for error messages.
        :returns: Boolean value.
        :raises ValueError: If value cannot be interpreted as boolean.
        """
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ('true', 'yes', '1', 'on'):
                return True
            elif value.lower() in ('false', 'no', '0', 'off'):
                return False
        raise ValueError(f"Invalid {field_name}: {value}")

    @staticmethod
    def ensure_string(value: Any, default: str, field_name: str = "value") -> str:
        """
        Ensure the value is a string.

        :param value: Raw input value.
        :param default: Default value if input is None.
        :param field_name: Name of the field for consistency.
        :returns: String value.
        """
        if value is None:
            return default
        return str(value)

    @staticmethod
    def parse_log_level(level: str) -> LogLevel:
        """
        Convert a string to a LogLevel enum.

        :param level: Raw log level string.
        :returns: LogLevel enum instance.
        :raises ValueError: If the string is not a valid log level.
        """
        try:
            return LogLevel(level.upper())
        except ValueError:
            raise ValueError(f"Invalid log level: {level}")

    @staticmethod
    def parse_theme_mode(mode: str) -> AppTheme:
        """
        Convert a string to an AppTheme enum.

        :param mode: Raw theme mode string.
        :returns: AppTheme enum instance.
        :raises ValueError: If the string is not a valid theme.
        """
        try:
            return AppTheme(mode.upper())
        except ValueError:
            raise ValueError(f"Invalid theme mode: {mode}")

    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> str:
        """
        Validate a file path and optionally check existence.

        :param path: File path to validate.
        :param must_exist: If True, the file must exist.
        :returns: Absolute, normalized file path.
        :raises ValueError: If must_exist is True and the file does not exist.
        """
        path_obj = Path(path)
        if must_exist and not path_obj.exists():
            raise ValueError(f"File not found: {path}")
        return str(path_obj)

    @staticmethod
    def validate_directory_path(path: str, create_if_missing: bool = False) -> str:
        """
        Validate or create a directory path.

        :param path: Directory path to validate.
        :param create_if_missing: Create directory if it does not exist.
        :returns: Absolute, normalized directory path.
        :raises ValueError: If the path is invalid and cannot be created.
        """
        path_obj = Path(path)
        if create_if_missing and not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
        return str(path_obj)

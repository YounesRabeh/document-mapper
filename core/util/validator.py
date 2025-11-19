from pathlib import Path
from typing import Any

from core.enums.app_themes import AppTheme
from core.enums.log_level import LogLevel


class ConfigValidator:
    """
    Validation and type-conversion utilities for configuration values.

    This class centralizes all input validation logic used when merging TOML and
    environment variables into the main application configuration. It ensures
    that values are properly typed and consistent before being injected into
    the final configuration dictionary.

    The validator supports:
    - Positive integer validation
    - Boolean parsing (from multiple string formats)
    - String fallback
    - Parsing enums such as LogLevel and AppTheme
    - File and directory path validation (auto-creation supported)

    All methods raise ValueError on invalid input, allowing callers to safely
    fall back to defaults or handle errors gracefully.
    """

    @staticmethod
    def ensure_positive_int(value: Any, default: int, field_name: str = "value") -> int:
        """
        Ensure that a configuration value represents a positive integer.

        Parameters
        ----------
        value : Any
            The raw value to validate (typically from TOML or .env).
        default : int
            Unused here, but kept for API symmetry with other validators.
        field_name : str, optional
            Name of the configuration field, included in error messages.

        Returns
        -------
        int
            Validated positive integer.

        Raises
        ------
        ValueError
            If the value cannot be converted to a positive integer.
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
        Ensure that a configuration value represents a boolean.

        Accepted truthy values:
            - "true", "yes", "1", "on"

        Accepted falsy values:
            - "false", "no", "0", "off"

        Parameters
        ----------
        value : Any
            The input value to evaluate.
        default : bool
            Unused here; present for API consistency.
        field_name : str, optional
            Name of the field for error-reporting.

        Returns
        -------
        bool
            The parsed boolean value.

        Raises
        ------
        ValueError
            If the value cannot be interpreted as a boolean.
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
        Ensure a configuration value is converted to a string.

        Parameters
        ----------
        value : Any
            The input value.
        default : str
            Default return value if the input is None.
        field_name : str
            Included for consistency and potential future use.

        Returns
        -------
        str
            The value converted to string, or the default if the input is None.
        """
        if value is None:
            return default
        return str(value)

    @staticmethod
    def parse_log_level(level: str) -> LogLevel:
        """
        Parse a log level string and convert it into a LogLevel enum.

        Parameters
        ----------
        level : str
            Raw log level string (case-insensitive).

        Returns
        -------
        LogLevel
            Matching enum instance.

        Raises
        ------
        ValueError
            If the string does not correspond to any LogLevel.
        """
        try:
            return LogLevel(level.upper())
        except ValueError:
            raise ValueError(f"Invalid log level: {level}")

    @staticmethod
    def parse_theme_mode(mode: str) -> AppTheme:
        """
        Parse a theme mode string and convert it into an AppTheme enum.

        Parameters
        ----------
        mode : str
            Raw theme mode string (case-insensitive).

        Returns
        -------
        AppTheme
            Matching enum instance.

        Raises
        ------
        ValueError
            If the string does not match any available AppTheme.
        """
        try:
            return AppTheme(mode.upper())
        except ValueError:
            raise ValueError(f"Invalid theme mode: {mode}")

    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False) -> str:
        """
        Validate that a file path is syntactically correct and optionally exists.

        Parameters
        ----------
        path : str
            The filesystem path to validate.
        must_exist : bool, optional
            Whether to require that the file already exists.

        Returns
        -------
        str
            The absolute, normalized file path.

        Raises
        ------
        ValueError
            If the file must exist but does not.
        """
        path_obj = Path(path)
        if must_exist and not path_obj.exists():
            raise ValueError(f"File not found: {path}")
        return str(path_obj)

    @staticmethod
    def validate_directory_path(path: str, create_if_missing: bool = False) -> str:
        """
        Validate or create a directory path.

        Parameters
        ----------
        path : str
            The directory path to validate.
        create_if_missing : bool, optional
            If True, missing directories will be created recursively.

        Returns
        -------
        str
            The absolute, normalized directory path.

        Raises
        ------
        ValueError
            If the path is invalid and cannot be created.
        """
        path_obj = Path(path)
        if create_if_missing and not path_obj.exists():
            path_obj.mkdir(parents=True, exist_ok=True)
        return str(path_obj)

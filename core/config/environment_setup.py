"""
EnvironmentSetup Module
=======================

This module provides unified configuration loading for Python applications.
It automatically loads and merges values from:

- `config.toml` (always)
- `.env` (only when running in development mode)
- Environment variables that override TOML values (dev mode)
- Automatic type casting & validation through `ConfigValidator`

It is compatible both with normal development execution and PyInstaller bundles.
The module also configures logging behavior based on loaded settings.
"""

import os
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from core.util.logger import Logger

# TOML: built-in in Python 3.11+, fallback to tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from core.util.validator import ConfigValidator


class EnvironmentSetup:
    """
    Handles environment configuration loading for both development and production modes.

    This class loads `config.toml`, and optionally `.env`, merges their values,
    performs type casting and validation, and configures logging based on the
    resulting configuration.

    Features
    --------
    - Detects PyInstaller environment (`_MEIPASS`)
    - Loads and parses TOML configuration
    - Optionally loads `.env` (dev mode only)
    - Automatically casts types using `ConfigValidator`
    - Resolves file/directory paths and creates directories if needed
    - Configures logging using either `.env` or TOML settings
    - Returns a flattened dictionary of all settings

    Parameters
    ----------
    env_path : str, optional
        Name or path of the `.env` file (default: ".env").
    toml_path : str, optional
        Name or path of the TOML config file (default: "config.toml").
    """

    def __init__(self, env_path: str = ".env", toml_path: str = "config.toml"):
        self.validator = ConfigValidator()

        # Determine project root (works in both PyInstaller & dev)
        if hasattr(sys, "_MEIPASS"):
            # PyInstaller bundle
            self.project_root = Path(getattr(sys, "_MEIPASS")).resolve()
            self.is_dev = False
        else:
            # Normal dev run
            self.project_root = Path.cwd().resolve()
            self.is_dev = True  # True is correct, but we disable dev mode for testing

        self.toml_path = (self.project_root / toml_path).resolve()
        self.env_path = (self.project_root / env_path).resolve()

        # Load TOML (always)
        self.toml_data = self._load_toml()

        # Load .env only if running in dev mode
        self.env_loaded = False
        if self.is_dev and self.env_path.exists():
            load_dotenv(dotenv_path=self.env_path)
            self.env_loaded = True
            Logger.configure_from_env()
        elif self.is_dev:
            Logger.warning(f".env not found at {self.env_path}, skipping...")
        else:
            # Not in dev mode → use TOML-based logging
            self._configure_logging_from_toml()

    def _configure_logging_from_toml(self):
        """
        Configure logging using TOML settings when not running in development mode.

        This method reads logging settings from the loaded TOML configuration.
        If persistence logging is enabled, it injects environment variables that
        the logging system depends on.

        Behavior:
        - If TOML exists and defines `[logging].persistence_logging = true`,
          then PERSISTENCE_LOGGING is enabled.
        - The application name is passed via PERSISTENCE_LOGGING_TARGET_NAME.
        """
        if self.toml_data is not None:
            persistence_logging = (
                self.toml_data.get("logging", {}).get("persistence_logging", False)
            )
            if persistence_logging:
                os.environ["PERSISTENCE_LOGGING"] = "True"
                app_name = self.toml_data.get("app", {}).get("name")
                os.environ["PERSISTENCE_LOGGING_TARGET_NAME"] = app_name
        else:
            # Default: enable persistence logging
            os.environ["PERSISTENCE_LOGGING"] = "True"

        Logger.configure_from_env(self.project_root)

    def _load_toml(self) -> dict[str, Any] | None:
        """
        Load and parse the TOML configuration file.

        Returns
        -------
        dict[str, Any] | None
            Parsed TOML data, or None if the file does not exist.
        """
        if not self.toml_path.exists():
            return None
        with open(self.toml_path, "rb") as f:
            return tomllib.load(f)

    def _auto_cast(self, key: str, value: str) -> Any:
        """
        Automatically infer and cast environment variable values to the correct types.

        The method tries the following cast rules:
        - Special keys:
            * LOG_LEVEL → parsed using validator.parse_log_level
            * THEME_MODE → parsed using validator.parse_theme_mode
        - Boolean (true/false strings)
        - Positive integer
        - File or directory path (absolute, validated, directories created if needed)
        - Default: return as string

        Parameters
        ----------
        key : str
            Name of the configuration key.
        value : str
            Raw string value to cast.

        Returns
        -------
        Any
            The Casted Python object.
        """
        v = self.validator

        if key == "LOG_LEVEL":
            return v.parse_log_level(value)
        if key == "THEME_MODE":
            return v.parse_theme_mode(value)

        # Try boolean
        try:
            return v.ensure_boolean(value, False, key)
        except ValueError:
            pass

        # Try positive integer
        try:
            return v.ensure_positive_int(value, 0, key)
        except ValueError:
            pass

        # Path auto-handling
        if any(x in key for x in ("PATH", "DIR", "FILE")):
            p = Path(value).expanduser().resolve()
            if p.suffix:
                return v.validate_file_path(str(p))
            return v.validate_directory_path(str(p), create_if_missing=True)

        # Default: string
        return v.ensure_string(value, "", key)

    def load(self) -> dict:
        """
        Load, merge, flatten, and return the final application configuration.

        The result includes:
        - Flattened TOML values (e.g. `[app].name` → `APP_NAME`)
        - .env overrides (dev mode only)
        - Auto-casted types for `.env` values
        - A meta-flag `IS_DEV_MODE`

        Returns
        -------
        dict
            A flat configuration dictionary with merged values.
        """
        config = {}

        if self.toml_data is None:
            Logger.error(f"Failed to load TOML configuration from {self.toml_path}")
            return config

        # Flatten TOML sections
        for section, values in self.toml_data.items():
            for key, value in values.items():
                config[f"{section.upper()}_{key.upper()}"] = value

        # Merge `.env` overrides
        if self.env_loaded:
            for key, value in os.environ.items():
                if key.isupper():
                    try:
                        config[key] = self._auto_cast(key, value)
                    except Exception:
                        config[key] = value  # Fallback

        # Add meta flag
        config["IS_DEV_MODE"] = self.is_dev
        return config

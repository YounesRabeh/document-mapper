import os
import sys
from pathlib import Path
from typing import Any
from dotenv import load_dotenv

from core.enums.log_level import LogLevel
from core.util.logger import Logger

# TOML: built-in in Python 3.11+, fallback to tomli for older versions
try:
    import tomllib
except ImportError:
    import tomli as tomllib

from core.util.validator import ConfigValidator


class EnvironmentSetup:
    """Load and merge config.toml and .env (only in dev mode)."""

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
            self.is_dev = True # True is correct, but we disable dev mode for testing

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
            if self.toml_data is not None:
                persistence_logging = (
                    self.toml_data.get("logging", {}).get("persistence_logging", False)
                )
                if persistence_logging:
                    os.environ["PERSISTENCE_LOGGING"] = "True"
                    app_name = self.toml_data.get("app", {}).get("name")
                    os.environ["PERSISTENCE_LOGGING_TARGET_NAME"] = app_name
            else:
                os.environ["PERSISTENCE_LOGGING"] = "True"
            Logger.configure_from_env(self.project_root)

    def _load_toml(self) -> dict[str, Any] | None | Any:
        if not self.toml_path.exists():
            return None
        with open(self.toml_path, "rb") as f:
            return tomllib.load(f)

    def _auto_cast(self, key: str, value: str):
        """Validate and cast types using ConfigValidator."""
        v = self.validator

        if key == "LOG_LEVEL":
            return v.parse_log_level(value)
        if key == "THEME_MODE":
            return v.parse_theme_mode(value)

        try:
            return v.ensure_boolean(value, False, key)
        except ValueError:
            pass
        try:
            return v.ensure_positive_int(value, 0, key)
        except ValueError:
            pass

        if any(x in key for x in ("PATH", "DIR", "FILE")):
            p = Path(value).expanduser().resolve()
            if p.suffix:
                return v.validate_file_path(str(p))
            return v.validate_directory_path(str(p), create_if_missing=True)

        return v.ensure_string(value, "", key)

    def load(self) -> dict:
        """Merge TOML and (optionally) .env into a flat dict."""
        config = {}

        if self.toml_data is None:
            Logger.error(f"Failed to load TOML configuration from {self.toml_path}")
            return config

        # Flatten TOML sections
        for section, values in self.toml_data.items():
            for key, value in values.items():
                config[f"{section.upper()}_{key.upper()}"] = value

        # Merge .env values (only in dev mode)
        if self.env_loaded:
            for key, value in os.environ.items():
                if key.isupper():
                    try:
                        config[key] = self._auto_cast(key, value)
                    except Exception:
                        config[key] = value

        # Add meta flag
        config["IS_DEV_MODE"] = self.is_dev
        return config

import sys
from pathlib import Path
from dotenv import load_dotenv
from core.util.validator import ConfigValidator
import os

class ConfigLoader:
    """Load and validate environment variables into a normal dictionary."""

    def __init__(self, env_path: str = ".env"):
        # Check multiple possible locations
        possible_paths = [Path(env_path)]

        # If running as a PyInstaller bundle
        if hasattr(sys, "_MEIPASS"):
            possible_paths.append(Path(sys._MEIPASS) / env_path)

        # Find first existing
        for path in possible_paths:
            if path.exists():
                self.env_path = path
                break
        else:
            self.env_path = possible_paths[0]
            print(f"[WARN] .env file not found at {self.env_path}, continuing without it.")
            return

        load_dotenv(dotenv_path=self.env_path)
        self.validator = ConfigValidator()

    def _auto_cast(self, key: str, value: str):
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
        config = {}
        for key, value in os.environ.items():
            if key.isupper():
                try:
                    config[key] = self._auto_cast(key, value)
                except Exception:
                    config[key] = value
        return config

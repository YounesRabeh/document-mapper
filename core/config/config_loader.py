import os
from pathlib import Path
from dotenv import load_dotenv
from core.util.validator import ConfigValidator


class ConfigLoader:
    """Load and validate environment variables into a normal dictionary."""

    def __init__(self, env_path: str = ".env"):
        self.env_path = Path(env_path)
        if not self.env_path.exists():
            raise FileNotFoundError(f".env file not found at: {self.env_path}")

        load_dotenv(dotenv_path=self.env_path)
        self.validator = ConfigValidator()

    def _auto_cast(self, key: str, value: str):
        """Infer and validate types automatically."""
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

        # Try integer
        try:
            return v.ensure_positive_int(value, 0, key)
        except ValueError:
            pass

        # Try path (normalize automatically)
        if any(x in key for x in ("PATH", "DIR", "FILE")):
            p = Path(value).expanduser().resolve()
            if p.suffix:  # has a file extension
                return v.validate_file_path(str(p))
            return v.validate_directory_path(str(p), create_if_missing=True)

        # Default to string
        return v.ensure_string(value, "", key)

    def load(self) -> dict:
        """Load all env variables into a validated dictionary."""
        config = {}
        for key, value in os.environ.items():
            if key.isupper():
                try:
                    config[key] = self._auto_cast(key, value)
                except Exception:
                    config[key] = value  # fallback to raw if validation fails
        return config

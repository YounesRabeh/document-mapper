from core.config.config_loader import ConfigLoader


class Config:
    """Singleton-style global configuration."""

    _instance = None

    @classmethod
    def get(cls):
        """Load config only once and reuse it globally."""
        if cls._instance is None:
            loader = ConfigLoader(".env")
            cls._instance = loader.load()
        return cls._instance

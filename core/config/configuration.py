from core.config.config_loader import ConfigLoader

class Config:
    """Singleton global config (auto merges config.toml + .env in dev)."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            loader = ConfigLoader()
            cls._instance = loader.load()
        return cls._instance

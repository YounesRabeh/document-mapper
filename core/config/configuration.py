from core.config.environment_setup import EnvironmentSetup
from core.util.logger import Logger


class _SafeConfig(dict):
    """A dict-like config wrapper that warns when a key is missing."""

    def get(self, key, default=None):
        value = super().get(key, default)

        if key in self:
            Logger.debug(f"Retrieved key '{key}': {value!r}")
        elif default is None:
            Logger.error(f"Missing key '{key}' in configuration!")
        else:
            Logger.warning(f"Key '{key}' not found, using default: {default!r}")

        return value



class Config:
    """Singleton global config (auto merges config.toml + .env in dev)."""

    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            environment = EnvironmentSetup()
            loaded = environment.load()
            Logger.debug(f"Loaded configuration")

            # Ensure we return a SafeConfig
            if not isinstance(loaded, _SafeConfig):
                cls._instance = _SafeConfig(loaded)
            else:
                cls._instance = loaded

        return cls._instance

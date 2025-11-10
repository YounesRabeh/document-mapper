from typing import Optional
from core.config.environment_setup import EnvironmentSetup
from core.util.logger import Logger

"""
Configuration helpers for the application.

This module exposes:
- `_SafeConfig`: a thin dict-like wrapper that logs accesses and warns/errors when keys are missing.
- `Config`: a singleton accessor that loads application configuration via `EnvironmentSetup`
  and returns a `_SafeConfig` instance.

All configuration access is logged through `Logger` for visibility during debugging
and runtime diagnostics.
"""


class _SafeConfig(dict):
    """
    A dict-like configuration wrapper that logs accesses and warns when a key is missing.

    Behavior:
    - If a key exists, the value is returned and a debug message is emitted.
    - If a key does not exist and no default is provided, an error is logged.
    - If a key does not exist and a default is provided, a warning is logged and the
      default value is returned.

    This class subclasses :class:`dict`, so it can be used wherever a standard mapping
    is expected.
    """

    def get(self, key, default=None):
        """
        Retrieve a configuration value by key.

        :param key: The configuration key to retrieve.
        :param default: The value to return if the key is not present.
                        If omitted (``None``), missing keys are logged as an error.
        :returns: The value for the key if present, otherwise the default.
        """
        value = super().get(key, default)

        if key in self:
            Logger.debug(f"Retrieved key '{key}': {value!r}")
        elif default is None:
            Logger.error(f"Missing key '{key}' in configuration!")
        else:
            Logger.warning(f"Key '{key}' not found, using default: {default!r}")

        return value


class Config:
    """
    Singleton global configuration accessor.

    This class ensures configuration is loaded once and shared across the application.
    It automatically merges configuration sources (e.g. ``config.toml`` and ``.env`` files)
    in development mode.

    :cvar _instance: Cached :class:`_SafeConfig` instance used throughout the application.
    """

    _instance: Optional[_SafeConfig] = None

    @classmethod
    def get(cls) -> _SafeConfig:
        """
        Retrieve the global configuration instance.

        :returns: The singleton configuration object.
        :rtype: _SafeConfig
        """
        if cls._instance is None:
            environment = EnvironmentSetup()
            loaded = environment.load()
            Logger.debug("Loaded configuration")

            # Ensure we return a SafeConfig
            cls._instance = _SafeConfig(loaded) if not isinstance(loaded, _SafeConfig) else loaded

        return cls._instance

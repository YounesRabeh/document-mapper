import os
import sys
from types import MethodType
from typing import Optional
from pathlib import Path

from core.util.logger import Logger


class Resources:
    """
    Dynamic resource manager for handling application assets in both development
    and bundled environments (e.g., PyInstaller).

    This class provides a centralized way to access and manage application
    resources such as icons, images, fonts, QSS files, or data. It automatically
    handles differences between development (source files on disk) and bundled
    environments (resources embedded by tools like PyInstaller).

    Features:
    -----------
    - Resolves base paths depending on environment (dev vs bundled).
    - Indexes all files in resource directories for fast access.
    - Provides dynamic getter methods:
        - get_in_<resource>(filename_or_path): returns the absolute path to a resource.
        - get_all_in_<resource>(): returns all files for a given resource type.
    - Automatically creates required directories in development mode.
    - Logs errors and warnings when resources are missing or misconfigured.

    Attributes:
    -----------
    _cfg : dict
        Stores the normalized resource configuration loaded from application config.
    _resources : dict
        Indexed list of all files for each resource type.
    _is_bundled : bool
        True if the application is running as a frozen/bundled executable.

    Methods:
    --------
    _get_base_path() -> Path
        Returns the base path for resources depending on environment.
    _list_files(directory: str) -> list[str]
        Recursively lists all files in the given directory.
    _create_get_all_method(name: str)
        Dynamically creates get_all_<name>() method for accessing all files.
    _create_get_method(name: str)
        Dynamically creates get_<name>(filename_or_path) method for accessing a single file.
    initialize(cfg: Optional[dict] = None)
        Initializes the resource manager with configuration, indexes all files,
        creates getter methods, and prepares directories if needed.
    get_all() -> dict[str, list[str]]
        Returns the dictionary of all indexed resources.
    """

    _cfg = {}
    _resources = {}
    _is_bundled = getattr(sys, 'frozen', False)

    @classmethod
    def _get_base_path(cls):
        """Get the base path for resources (works in both dev and bundled env)."""
        if cls._is_bundled:
            # In bundled app, resources are in _internal folder
            return Path(sys._MEIPASS) / "resources"
        else:
            # In development, use project root
            return Path.cwd() / "resources"

    @classmethod
    def _list_files(cls, directory: str) -> list[str]:
        """Recursively list all files in a directory."""
        files = []
        if not os.path.exists(directory):
            return files
        for root, _, filenames in os.walk(directory):
            for f in filenames:
                files.append(os.path.join(root, f))
        return files

    @classmethod
    def _create_get_all_method(cls, name: str):
        """Create get_all_<name>()"""

        def method(self_or_cls):
            return cls._resources.get(name, [])

        method.__name__ = f"get_all_in_{name}"
        setattr(cls, method.__name__, MethodType(method, cls))

    @classmethod
    def _create_get_method(cls, name: str):
        """Create get_in_<name>(filename_or_path)"""

        def method(self_or_cls, path: str, suppress: bool = False):
            base_path = getattr(cls, name)

            # Try direct path first
            if os.path.exists(path):
                return os.path.abspath(path)

            # Try relative to base path
            candidate = os.path.join(base_path, path)
            if os.path.exists(candidate):
                return os.path.abspath(candidate)

            # Try in bundled location
            if cls._is_bundled:
                bundled_candidate = os.path.join(cls._get_base_path(), path)
                if os.path.exists(bundled_candidate):
                    return os.path.abspath(bundled_candidate)

            Logger.error(f"Resource not found: {path}")
            if not suppress:
                raise FileNotFoundError(f"Resource not found: {path}")
            return None  # Return None if suppression is active

        method.__name__ = f"get_in_{name}"
        setattr(cls, method.__name__, MethodType(method, cls))

    @classmethod
    def initialize(cls, cfg: Optional[dict] = None):
        if cfg is not None:
            cls._cfg = {k.replace("RESOURCES_", "").lower(): v
                        for k, v in cfg.items() if k.startswith("RESOURCES_")}
        elif not hasattr(cls, "_cfg") or not cls._cfg:
            Logger.error("No configuration provided and Resources._cfg is empty!")
            return

        base_path = cls._get_base_path()

        for key, path in cls._cfg.items():
            if key == "base":
                setattr(cls, key, str(base_path))
                continue

            # In bundled app, resources are directly in _internal/resources/subfolder
            if cls._is_bundled:
                abs_path = base_path / key
            else:
                abs_path = Path(path) if Path(path).is_absolute() else base_path / Path(path).name

            setattr(cls, key, str(abs_path))

            # Only create directories in development mode
            if not cls._is_bundled:
                os.makedirs(abs_path, exist_ok=True)

            cls._resources[key] = cls._list_files(str(abs_path))
            cls._create_get_all_method(key)
            cls._create_get_method(key)

            Logger.debug(f"Indexed {len(cls._resources[key])} {key} files from: {abs_path}")

    @classmethod
    def get_all(cls) -> dict[str, list[str]]:
        """Return the dict of all indexed resources."""
        return cls._resources


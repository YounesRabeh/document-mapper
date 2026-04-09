from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths


class AppPaths:
    """Centralized resolver for writable app paths and bundled resources."""

    DEFAULT_APP_SLUG = "document-mapper"
    DEFAULT_PROJECT_DIRNAME = "document-mapper-project"
    DEFAULT_PROJECT_FILENAME = "project.json"
    DEFAULT_LOG_FILENAME = "generation.log"
    DEFAULT_RESOURCES_DIRNAME = "resources"
    DEFAULT_LOCALES_DIRNAME = "locales"

    @classmethod
    def is_bundled(cls) -> bool:
        """Return True when running from a frozen/bundled executable."""
        return hasattr(sys, "_MEIPASS")

    @classmethod
    def project_root(cls) -> Path:
        """Return repository root in development mode."""
        return Path(__file__).resolve().parents[2]

    @classmethod
    def bundle_root(cls) -> Path:
        """Return runtime root for resources (bundle root or project root)."""
        if cls.is_bundled():
            return Path(getattr(sys, "_MEIPASS")).resolve()
        return cls.project_root()

    @classmethod
    def resource_root(cls, resource_dirname: str = DEFAULT_RESOURCES_DIRNAME) -> Path:
        """Return absolute root directory for packaged resources."""
        return (cls.bundle_root() / resource_dirname).resolve()

    @classmethod
    def app_slug(cls) -> str:
        """Return a filesystem-safe app slug derived from application name."""
        app_name = ""
        instance = QCoreApplication.instance()
        if instance is not None:
            app_name = instance.applicationName()
        if not app_name:
            app_name = cls.DEFAULT_APP_SLUG
        slug = re.sub(r"[^a-z0-9]+", "-", str(app_name).strip().lower()).strip("-")
        return slug or cls.DEFAULT_APP_SLUG

    @classmethod
    def _writable_location(cls, location: QStandardPaths.StandardLocation) -> Path:
        resolved = QStandardPaths.writableLocation(location)
        if resolved:
            return Path(resolved).expanduser().resolve()

        fallback_map = {
            QStandardPaths.StandardLocation.StateLocation: Path.home() / ".local" / "state" / cls.app_slug(),
            QStandardPaths.StandardLocation.CacheLocation: Path.home() / ".cache" / cls.app_slug(),
            QStandardPaths.StandardLocation.DocumentsLocation: Path.home() / "Documents",
        }
        return fallback_map.get(location, Path.home()).resolve()

    @classmethod
    def state_dir(cls) -> Path:
        """Return writable state directory, creating it if needed."""
        path = cls._writable_location(QStandardPaths.StandardLocation.StateLocation)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def cache_dir(cls) -> Path:
        """Return writable cache directory, creating it if needed."""
        path = cls._writable_location(QStandardPaths.StandardLocation.CacheLocation)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def documents_dir(cls) -> Path:
        """Return user documents directory, creating it if needed."""
        path = cls._writable_location(QStandardPaths.StandardLocation.DocumentsLocation)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def logs_dir(cls) -> Path:
        """Return app log directory under state storage."""
        path = cls.state_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def default_project_path(cls) -> Path:
        """Return default project location used by save/open flows."""
        return cls.internal_project_dir()

    @classmethod
    def internal_project_dir(cls) -> Path:
        """Return writable internal project directory."""
        path = cls.state_dir() / cls.DEFAULT_PROJECT_DIRNAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def default_log_path(cls) -> Path:
        """Return default persistent log file path."""
        return cls.logs_dir() / cls.DEFAULT_LOG_FILENAME

    @classmethod
    def legacy_resources_temp_dir(cls) -> Path:
        """Return legacy temp resource directory path used by migrations."""
        return cls.project_root() / cls.DEFAULT_RESOURCES_DIRNAME / "temp"

    @classmethod
    def legacy_last_session_path(cls, filename: str) -> Path:
        """Return legacy last-session file path for migration logic."""
        return cls.legacy_resources_temp_dir() / filename

    @classmethod
    def locales_dir(cls) -> Path | None:
        """Return locale directory if available in current runtime layout."""
        candidate = cls.resource_root() / cls.DEFAULT_LOCALES_DIRNAME
        if candidate.exists():
            return candidate.resolve()
        return None

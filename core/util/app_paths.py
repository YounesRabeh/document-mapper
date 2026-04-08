from __future__ import annotations

import re
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths


class AppPaths:
    DEFAULT_APP_SLUG = "document-mapper"
    DEFAULT_PROJECT_DIRNAME = "document-mapper-project"
    DEFAULT_PROJECT_FILENAME = "project.json"
    DEFAULT_LOG_FILENAME = "generation.log"
    DEFAULT_RESOURCES_DIRNAME = "resources"
    DEFAULT_LOCALES_DIRNAME = "locales"

    @classmethod
    def is_bundled(cls) -> bool:
        return hasattr(sys, "_MEIPASS")

    @classmethod
    def project_root(cls) -> Path:
        return Path(__file__).resolve().parents[2]

    @classmethod
    def bundle_root(cls) -> Path:
        if cls.is_bundled():
            return Path(getattr(sys, "_MEIPASS")).resolve()
        return cls.project_root()

    @classmethod
    def resource_root(cls, resource_dirname: str = DEFAULT_RESOURCES_DIRNAME) -> Path:
        return (cls.bundle_root() / resource_dirname).resolve()

    @classmethod
    def app_slug(cls) -> str:
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
        path = cls._writable_location(QStandardPaths.StandardLocation.StateLocation)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def cache_dir(cls) -> Path:
        path = cls._writable_location(QStandardPaths.StandardLocation.CacheLocation)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def documents_dir(cls) -> Path:
        path = cls._writable_location(QStandardPaths.StandardLocation.DocumentsLocation)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def logs_dir(cls) -> Path:
        path = cls.state_dir() / "logs"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def default_project_path(cls) -> Path:
        return cls.internal_project_dir()

    @classmethod
    def internal_project_dir(cls) -> Path:
        path = cls.state_dir() / cls.DEFAULT_PROJECT_DIRNAME
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def default_log_path(cls) -> Path:
        return cls.logs_dir() / cls.DEFAULT_LOG_FILENAME

    @classmethod
    def legacy_resources_temp_dir(cls) -> Path:
        return cls.project_root() / cls.DEFAULT_RESOURCES_DIRNAME / "temp"

    @classmethod
    def legacy_last_session_path(cls, filename: str) -> Path:
        return cls.legacy_resources_temp_dir() / filename

    @classmethod
    def locales_dir(cls) -> Path | None:
        candidate = cls.resource_root() / cls.DEFAULT_LOCALES_DIRNAME
        if candidate.exists():
            return candidate.resolve()
        return None

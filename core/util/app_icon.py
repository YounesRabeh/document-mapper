from __future__ import annotations

import ctypes
import os
import re
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from core.util.app_paths import AppPaths
from core.util.logger import Logger
from core.util.resources import Resources

DESKTOP_FILE_NAME = "document-mapper"
DESKTOP_ENTRY_FILENAME = f"{DESKTOP_FILE_NAME}.desktop"


@dataclass(frozen=True)
class ApplicationIntegrationTarget:
    """Platform-specific integration target derived from the current runtime/build OS."""

    platform: str
    desktop_file_name: str | None = None
    desktop_entry_filename: str | None = None
    windows_app_user_model_id: str | None = None


def current_platform_family() -> str:
    """Return a stable platform family name for integration decisions."""
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    return sys.platform


def _normalize_app_id_segment(value: str) -> str:
    """Return a compact segment safe for Windows AppUserModelID parts."""
    return re.sub(r"[^a-z0-9]+", "", value.strip().lower())


def build_application_identifier(
    *,
    app_name: str,
    organization_name: str = "",
    organization_domain: str = "",
) -> str:
    """Build a stable cross-platform application identifier from config metadata."""
    normalized_domain = organization_domain.strip().lower()
    normalized_domain = normalized_domain.split("://")[-1]
    normalized_domain = normalized_domain.split("/")[0]
    normalized_domain = normalized_domain.split(":")[0]

    domain_parts: list[str] = []
    for part in reversed(normalized_domain.split(".")):
        normalized_part = _normalize_app_id_segment(part)
        if normalized_part:
            domain_parts.append(normalized_part)
    organization_part = _normalize_app_id_segment(organization_name)
    app_part = _normalize_app_id_segment(app_name) or _normalize_app_id_segment(DESKTOP_FILE_NAME)

    parts: list[str] = list(domain_parts)
    if organization_part and organization_part not in parts:
        parts.append(organization_part)
    if app_part and (not parts or parts[-1] != app_part):
        parts.append(app_part)

    if not parts:
        parts = [_normalize_app_id_segment(DESKTOP_FILE_NAME), "app"]
    elif len(parts) == 1:
        parts.append("app")

    identifier = ".".join(part for part in parts if part).strip(".")
    return (identifier[:128].rstrip(".")) or f"{_normalize_app_id_segment(DESKTOP_FILE_NAME)}.app"


def detect_application_integration(
    *,
    app_name: str,
    organization_name: str = "",
    organization_domain: str = "",
) -> ApplicationIntegrationTarget:
    """Detect which platform integration should be created for the current environment."""
    platform = current_platform_family()
    if platform == "linux":
        return ApplicationIntegrationTarget(
            platform=platform,
            desktop_file_name=DESKTOP_FILE_NAME,
            desktop_entry_filename=DESKTOP_ENTRY_FILENAME,
        )
    if platform == "windows":
        return ApplicationIntegrationTarget(
            platform=platform,
            windows_app_user_model_id=build_application_identifier(
                app_name=app_name,
                organization_name=organization_name,
                organization_domain=organization_domain,
            ),
        )
    return ApplicationIntegrationTarget(platform=platform)


def _set_windows_app_user_model_id(app_user_model_id: str) -> bool:
    """Set a Windows AppUserModelID when available so taskbar grouping/icon lookup works."""
    try:
        windll = getattr(ctypes, "windll", None)
        if windll is None or not hasattr(windll, "shell32"):
            return False
        result = windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_user_model_id)
        if result not in (0, None):
            Logger.warning(
                f"Could not set Windows AppUserModelID '{app_user_model_id}' (code {result}).",
                tag="app_icon",
            )
            return False
        return True
    except Exception as exc:  # noqa: BLE001
        Logger.warning(f"Could not set Windows AppUserModelID: {exc}", tag="app_icon")
        return False


def configure_qt_application_identity(
    *,
    app_name: str,
    organization_name: str = "",
    organization_domain: str = "",
) -> ApplicationIntegrationTarget:
    """Set Qt application metadata before QApplication is constructed."""
    QCoreApplication.setApplicationName(app_name)
    QCoreApplication.setOrganizationName(organization_name)
    QCoreApplication.setOrganizationDomain(organization_domain)
    integration = detect_application_integration(
        app_name=app_name,
        organization_name=organization_name,
        organization_domain=organization_domain,
    )
    if integration.desktop_file_name:
        QGuiApplication.setDesktopFileName(integration.desktop_file_name)
    if integration.windows_app_user_model_id:
        _set_windows_app_user_model_id(integration.windows_app_user_model_id)
    return integration


def resolve_app_icon_paths() -> list[Path]:
    """Return candidate icon paths from resources for runtime icon setup."""
    candidates: list[Path] = []
    get_icon = getattr(Resources, "get_in_icons", None)
    if callable(get_icon):
        resolved = get_icon("document-mapper.ico", suppress=True)
        if resolved:
            candidates.append(Path(resolved).expanduser().resolve())

    resources_icons = AppPaths.resource_root("resources") / "icons"
    candidate = (resources_icons / "document-mapper.ico").resolve()
    if candidate.exists() and candidate not in candidates:
        candidates.append(candidate)
    return candidates


def resolve_app_icon_path() -> Path | None:
    """Return the first available icon path, for compatibility and tests."""
    candidates = resolve_app_icon_paths()
    return candidates[0] if candidates else None


def build_app_icon() -> QIcon | None:
    """Build a QIcon from all available icon candidates."""
    icon = QIcon()
    for path in resolve_app_icon_paths():
        icon.addFile(str(path))
    return None if icon.isNull() else icon


def ensure_linux_desktop_integration(
    app_name: str,
    icon_paths: list[Path],
    *,
    entrypoint_path: Path | None = None,
):
    """Create/update Linux desktop metadata so docks can resolve the app icon."""
    if current_platform_family() != "linux":
        return

    try:
        xdg_data_home = Path(
            os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        ).expanduser().resolve()
        applications_dir = xdg_data_home / "applications"
        applications_dir.mkdir(parents=True, exist_ok=True)

        preferred_icon = next((path for path in icon_paths if path.suffix.lower() == ".png"), None)
        if preferred_icon is None and icon_paths:
            preferred_icon = icon_paths[0]
        if preferred_icon is None:
            return

        icon_target_dir = xdg_data_home / "icons" / "hicolor" / "512x512" / "apps"
        icon_target_dir.mkdir(parents=True, exist_ok=True)
        icon_target_path = icon_target_dir / "document-mapper.png"
        if _should_refresh_launcher_icon(preferred_icon, icon_target_path):
            _render_launcher_png(preferred_icon, icon_target_path)

        if getattr(sys, "frozen", False):
            exec_cmd = shlex.quote(str(Path(sys.executable).resolve()))
        else:
            target_entrypoint = (entrypoint_path or Path(sys.argv[0])).expanduser().resolve()
            exec_cmd = (
                f"{shlex.quote(str(Path(sys.executable).resolve()))} "
                f"{shlex.quote(str(target_entrypoint))}"
            )

        desktop_file = applications_dir / DESKTOP_ENTRY_FILENAME
        desktop_content = "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                f"Name={app_name}",
                "Comment=Document Mapper",
                f"Exec={exec_cmd}",
                f"Icon={icon_target_path}",
                "Terminal=false",
                "Categories=Office;Utility;",
                f"StartupWMClass={app_name}",
                f"X-GNOME-WMClass={app_name}",
                "",
            ]
        )
        if not desktop_file.exists() or desktop_file.read_text(encoding="utf-8") != desktop_content:
            desktop_file.write_text(desktop_content, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        Logger.warning(f"Could not update Linux desktop integration: {exc}", tag="app_icon")


def _should_refresh_launcher_icon(source_icon: Path, target_path: Path) -> bool:
    if not target_path.exists() or target_path.stat().st_size <= 0:
        return True
    return target_path.stat().st_mtime < source_icon.stat().st_mtime


def _render_launcher_png(source_icon: Path, target_png: Path):
    """Render a PNG launcher icon from the source icon file."""
    icon = QIcon(str(source_icon))
    if icon.isNull():
        return
    pixmap: QPixmap = icon.pixmap(512, 512)
    if pixmap.isNull():
        return
    pixmap.save(str(target_png), "PNG")


def apply_app_icon_setup(
    app: QApplication,
    *,
    app_name: str,
    entrypoint_path: Path | None = None,
) -> QIcon | None:
    """Apply desktop metadata and return app icon for app/window assignment."""
    icon_paths = resolve_app_icon_paths()
    ensure_linux_desktop_integration(
        app_name,
        icon_paths,
        entrypoint_path=entrypoint_path,
    )
    icon = build_app_icon()
    if icon is not None:
        app.setWindowIcon(icon)
    return icon

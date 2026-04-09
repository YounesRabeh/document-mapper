from __future__ import annotations

import os
import shlex
import sys
from pathlib import Path

from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication

from core.util.app_paths import AppPaths
from core.util.logger import Logger
from core.util.resources import Resources

DESKTOP_FILE_NAME = "document-mapper.desktop"


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
    if sys.platform != "linux":
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

        desktop_file = applications_dir / DESKTOP_FILE_NAME
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
    app.setDesktopFileName(DESKTOP_FILE_NAME)
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

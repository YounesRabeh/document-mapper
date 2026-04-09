from __future__ import annotations

from pathlib import Path

from core.util.app_paths import AppPaths
from core.util.resources import Resources


def _combo_arrow_path() -> str:
    getter = getattr(Resources, "get_in_icons", None)
    if getter is not None:
        resolved = getter("sys/chevron_down.svg", suppress=True)
        if resolved:
            return Path(resolved).resolve().as_posix()
    return (AppPaths.resource_root("resources") / "icons" / "sys" / "chevron_down.svg").as_posix()


def load_stylesheet(name: str) -> str:
    """Load a QSS file by logical name and inject runtime asset placeholders."""
    getter = getattr(Resources, "get_in_qss", None)
    if getter is not None:
        path = Path(getter(f"{name}.qss"))
    else:
        path = AppPaths.resource_root("resources") / "qss" / f"{name}.qss"
    qss = path.read_text(encoding="utf-8")
    return qss.replace("__COMBO_ARROW_PATH__", _combo_arrow_path())


def apply_stylesheet(widget, name: str):
    """Apply a named stylesheet to a widget."""
    widget.setStyleSheet(load_stylesheet(name))


__all__ = ["apply_stylesheet", "load_stylesheet"]

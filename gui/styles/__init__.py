from __future__ import annotations

from pathlib import Path

from core.util.resources import Resources


def _combo_arrow_path() -> str:
    resolved = Resources.get_in_icons("sys/chevron_down.svg", suppress=True)
    if resolved:
        return Path(resolved).resolve().as_posix()
    return (Path(__file__).resolve().parents[2] / "resources" / "icons" / "sys" / "chevron_down.svg").as_posix()


def load_stylesheet(name: str) -> str:
    path = Path(Resources.get_in_qss(f"{name}.qss"))
    qss = path.read_text(encoding="utf-8")
    return qss.replace("__COMBO_ARROW_PATH__", _combo_arrow_path())


def apply_stylesheet(widget, name: str):
    widget.setStyleSheet(load_stylesheet(name))


__all__ = ["apply_stylesheet", "load_stylesheet"]

import os
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QSizePolicy
from PySide6.QtGui import QPixmap, QAction, QFontMetrics
from PySide6.QtCore import Qt

from core.config.configuration import Config
from core.util.logger import Logger
from core.util.resources import Resources


def build_file_icon_map() -> dict[str, str]:
    """
    Build a map of file extensions to icon paths based on resources configuration.
    Each icon file can define multiple extensions separated by underscores.
    Example: 'docx_doc.png' -> maps both 'docx' and 'doc' to the same icon.
    """
    file_types_dir = Resources.get_in_icons("file_types")

    if not os.path.exists(file_types_dir):
        Logger.warning(f"File types icon directory not found: {file_types_dir}")
        return {}

    file_map = {}
    for filename in os.listdir(file_types_dir):
        if not filename.lower().endswith((".png", ".jpg", ".svg")):
            continue

        # Remove extension, split by underscores
        name_part = os.path.splitext(filename)[0]  # e.g., "docx_doc"
        extensions = name_part.split("_")           # ['docx', 'doc']

        icon_path = os.path.join(file_types_dir, filename)
        for ext in extensions:
            file_map[ext.lower()] = icon_path
    Logger.debug(f"File icon map: {file_map}")
    return file_map


# Pre-build icon map once
ICON_MAP = build_file_icon_map()


class FileEntry(QWidget):
    """
    A file-entry row that looks good in both dark and light themes,
    automatically displaying an icon based on the file extension.
    """


    def __init__(self, file_path: str, on_edit=None, on_delete=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.extension = self.file_name.split(".")[-1].lower()

        self.on_edit = on_edit
        self.on_delete = on_delete

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # ========== ICON ==========
        icon_label = QLabel()
        icon_label.setFixedSize(64, 64)
        pix = QPixmap(64, 64)
        pix.fill(Qt.darkGray)  # dark background for white icons
        icon_path = ICON_MAP.get(self.extension)
        if icon_path and os.path.exists(icon_path):
            icon_pix = QPixmap(icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pix = icon_pix
        icon_label.setPixmap(pix)

        # ========== TEXT ==========
        text_container = QVBoxLayout()
        text_container.setSpacing(2)

        name_label = QLabel(self.file_name)
        name_label.setStyleSheet("font-size: 14px;")
        name_label.setToolTip(self.file_name)
        # Stretch the name to take max space
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # File size
        size_bytes = os.path.getsize(self.file_path)
        size_str = self._format_size(size_bytes)
        info_label = QLabel(size_str)
        info_label.setStyleSheet("font-size: 11px; opacity: 0.6;")

        text_container.addWidget(name_label)
        text_container.addWidget(info_label)

        # ========== MENU BUTTON (▼) ==========
        menu_button = QPushButton("▼")  # single down arrow
        menu_button.setFixedSize(28, 28)
        menu_button.setCursor(Qt.PointingHandCursor)
        menu_button.setStyleSheet("""
            QPushButton {
                font-size: 14px;
                border: none;
                background: transparent;
                color: palette(window-text);
            }
            QPushButton:hover {
                color: palette(highlight);
            }
        """)

        menu = QMenu(self)
        action_edit = QAction("✏️ Edit", self)
        action_delete = QAction("⛔ Hide", self)
        menu.addAction(action_edit)
        menu.addAction(action_delete)
        menu_button.clicked.connect(
            lambda: menu.exec_(menu_button.mapToGlobal(menu_button.rect().bottomLeft()))
        )

        if self.on_edit:
            action_edit.triggered.connect(lambda: self.on_edit(self.file_path))
        if self.on_delete:
            action_delete.triggered.connect(lambda: self.on_delete(self.file_path))

        # ========== ASSEMBLE ==========
        layout.addWidget(icon_label)
        layout.addLayout(text_container)
        layout.addStretch()  # push menu button to the far right
        layout.addWidget(menu_button)

        # ========== UNIVERSAL STYLE ==========
        self.setStyleSheet("""
            FileEntry {
                background: rgba(255,255,255,0.03);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
            }
            FileEntry:hover {
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.18);
            }
        """)

    def _format_size(self, size_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"

    def paintEvent(self, event):
        super().paintEvent(event)
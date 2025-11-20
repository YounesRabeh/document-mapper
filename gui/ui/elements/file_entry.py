import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QAction
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QVBoxLayout, QPushButton, QMenu, QSizePolicy

from core.manager.theme_manager import ThemeManager
from core.util.logger import Logger
from core.util.resources import Resources
from core.util.system_info import open_in_libreoffice

FILE_TYPES_DIR_NAME = "file_types"
FILE_TYPES_ICON_SIZE = 64
FILE_TYPES_ICON_BG_COLOR = Qt.darkGray
FILE_TYPES_ICONS_EXTENSIONS = (".png", ".jpg", ".svg")
ICON_EXTENSION_SEPARATOR = "_"

def build_file_icon_map() -> dict[str, str]:
    """
    Build a map of file extensions to icon paths based on resources configuration.
    Each icon file can define multiple extensions separated by underscores.
    Example: 'docx_doc.png' -> maps both 'docx' and 'doc' to the same icon.
    """
    file_types_dir = Resources.get_in_icons(FILE_TYPES_DIR_NAME)

    if not os.path.exists(file_types_dir):
        Logger.warning(f"File types icon directory not found: {file_types_dir}")
        return {}

    file_map = {}
    for filename in os.listdir(file_types_dir):
        if not filename.lower().endswith(FILE_TYPES_ICONS_EXTENSIONS):
            continue

        # Remove extension, split by underscores
        name_part = os.path.splitext(filename)[0]  # e.g., "docx_doc"
        extensions = name_part.split(ICON_EXTENSION_SEPARATOR)    # ['docx', 'doc']

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
    DEFAULT_ICON, ERROR_ICON = None, None

    def __init__(self, file_path: str, on_edit=None, on_hide=None, parent=None):
        super().__init__(parent)
        # Lazy-load class-level icons if not already loaded
        if self.__class__.DEFAULT_ICON is None:
            self.__class__.DEFAULT_ICON = Resources.get_in_icons("sys/default_file_entry.png")
        if self.__class__.ERROR_ICON is None:
            self.__class__.ERROR_ICON = Resources.get_in_icons("sys/error.png")

        self.file_path = file_path
        self.file_exists = self.file_path is not None and os.path.exists(file_path)

        if not self.file_exists:
            self.file_name = "File not found !"
            Logger.error(f"File not found for path: '{self.file_path}'")
        else:
            self.file_name = os.path.basename(file_path)
        self.extension = self.file_name.split(".")[-1].lower()

        self.on_edit = on_edit if on_edit is not None else self.on_edit
        self.on_hide = on_hide if on_hide is not None else self.on_hide

        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # ========== ICON ==========
        icon_label = QLabel()
        icon_label.setFixedSize(FILE_TYPES_ICON_SIZE, FILE_TYPES_ICON_SIZE)

        # Determine which icon path to use
        icon_path = self.ERROR_ICON if not self.file_exists else ICON_MAP.get(self.extension)

        # Start with a blank pixmap with background color
        pix = QPixmap(FILE_TYPES_ICON_SIZE, FILE_TYPES_ICON_SIZE)
        pix.fill(FILE_TYPES_ICON_BG_COLOR)

        # If valid icon exists, load and scale it
        if icon_path and os.path.exists(icon_path):
            icon_pix = QPixmap(icon_path)
            if not icon_pix.isNull():
                pix = icon_pix.scaled(
                    FILE_TYPES_ICON_SIZE,
                    FILE_TYPES_ICON_SIZE,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
        icon_label.setPixmap(pix)

        # ========== TEXT ==========
        text_container = QVBoxLayout()
        text_container.setSpacing(2)

        name_label = QLabel(self.file_name)
        name_label.setObjectName("fileNameLabel")
        name_label.setToolTip(self.file_name)
        # Stretch the name to take max space
        name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # File size
        size_bytes = 0
        if self.file_exists:
            try:
                size_bytes = os.path.getsize(self.file_path)
            except Exception:
                Logger.warning(f"Could not get size for: {self.file_path}")
        size_label = QLabel(_format_size(size_bytes))
        size_label.setObjectName("sizeLabel")

        text_container.addWidget(name_label)
        text_container.addWidget(size_label)

        # ========== MENU BUTTON (▼) ==========
        menu_button = QPushButton("▼")  # single down arrow
        menu_button.setFixedSize(28, 28)
        menu_button.setCursor(Qt.PointingHandCursor)
        menu = QMenu(self)
        action_edit = QAction("✏️ Edit", self)
        action_hide = QAction("⛔ Hide", self)
        menu.addAction(action_edit)
        menu.addAction(action_hide)
        menu_button.clicked.connect(
            lambda: menu.exec_(menu_button.mapToGlobal(menu_button.rect().bottomLeft()))
        )

        if self.on_edit:
            action_edit.triggered.connect(lambda: self.on_edit(self.file_path))
        if self.on_hide:
            action_hide.triggered.connect(lambda: self.on_hide(self.file_path))

        # ========== ASSEMBLE ==========
        layout.addWidget(icon_label)
        layout.addLayout(text_container)
        layout.addStretch()  # push menu button to the far right
        layout.addWidget(menu_button)

        # ========== UNIVERSAL STYLE ==========
        ThemeManager.apply_theme_to_widget(self, Resources.get_in_qss("elements/file_entry/default.qss"))

    def paintEvent(self, event):
        super().paintEvent(event)

    def on_edit(self, file_path):
        """Callback when Edit is selected."""
        open_in_libreoffice(file_path)

    def on_hide(self, file_path):
        """Callback when hide is selected."""
        pass

def _format_size(size_bytes):
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"

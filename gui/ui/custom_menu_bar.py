from PySide6.QtGui import QKeySequence, QIcon
from PySide6.QtWidgets import QMessageBox
from core.manager.theme_manager import ThemeManager
from core.util.logger import Logger


class CustomMenuBar:
    """Centralized reusable menu bar definitions."""

    @staticmethod
    def default(stage):
        """
        Returns:
             a default menu structure compatible with UIFactory.create_menu_bar.
        `stage` is the QWidget (e.g. BaseStage subclass) that defines menu handlers.
        """
        return {
            "File": [
                ("New Project", None, None),
                ("Settings", None, None),
                (None, None),  # separator
                ("Exit", None, None),
            ],
            "View": [
                ("Toggle Theme", ThemeManager.toggle_theme, None),
            ],
            "Help": [
                ("About", None, None),
            ]
        }
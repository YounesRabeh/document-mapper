from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QMenuBar, QMenu
)
from PySide6.QtCore import Qt

from gui.ui.drag_drop import DragDrop


class UIFactory:
    """Reusable factory for building common UI elements."""

    @staticmethod
    def create_label(text: str, align=Qt.AlignCenter) -> QLabel:
        label = QLabel(text)
        label.setAlignment(align)
        return label

    @staticmethod
    def create_button(text: str, on_click=None) -> QPushButton:
        """Creates a styled QPushButton."""
        btn = QPushButton(text)
        if on_click:
            btn.clicked.connect(on_click)
        btn.setMinimumWidth(120)
        return btn

    @staticmethod
    def create_menu_bar(menu_structure: dict, parent: QWidget) -> QMenuBar:
        menubar = QMenuBar(parent)
        for menu_name, actions in menu_structure.items():
            menu = QMenu(menu_name, parent)
            for action_entry in actions:
                # Separator
                if action_entry[0] is None:
                    menu.addSeparator()
                    continue

                text, callback, *rest = action_entry
                shortcut = rest[0] if rest else None

                action = QAction(text, parent)
                if shortcut:
                    action.setShortcut(shortcut)
                if callback:
                    action.triggered.connect(callback)
                menu.addAction(action)

            menubar.addMenu(menu)
        return menubar

    @staticmethod
    def create_drag_drop_area(width, height, allowed_extensions=None, on_files_selected=None):
        """Creates a drag-drop area that supports click and drag-drop operations."""
        drag_drop = DragDrop()
        return drag_drop.create_drag_drop_area(width, height, allowed_extensions, on_files_selected)

    @staticmethod
    def create_file_entry(file_path, on_edit=None, on_delete=None, parent=None):
        from gui.ui.FileEntry import FileEntry
        return FileEntry(file_path, on_edit, on_delete, parent)
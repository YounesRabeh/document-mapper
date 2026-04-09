from __future__ import annotations

from PySide6.QtWidgets import QComboBox


class ClickSelectComboBox(QComboBox):
    """A combo box that ignores mouse-wheel changes unless the popup list is open."""

    def wheelEvent(self, event):
        """Allow wheel changes only while popup is visible to avoid accidental edits."""
        if self.view().isVisible():
            super().wheelEvent(event)
            return
        event.ignore()

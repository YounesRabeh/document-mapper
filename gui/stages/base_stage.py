from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal


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


class BaseStage(QWidget):
    """Base class shared by all stages with bottom navigation buttons."""

    next_stage = Signal()
    prev_stage = Signal()

    def __init__(self, config: dict, title: str):
        super().__init__()
        self.config = config
        self.title = title

        # ---- Main Layout ----
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)

        # Title
        self.main_layout.addWidget(UIFactory.create_label(self.title))

        # Content Area
        self.content_layout = QVBoxLayout()
        self.main_layout.addLayout(self.content_layout)

        # Spacer to push buttons to bottom
        self.main_layout.addStretch(1)

        # Bottom Navigation Bar
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(0, 10, 0, 0)
        self.nav_layout.setSpacing(20)
        self.main_layout.addLayout(self.nav_layout)

    def add_nav_buttons(self, back_text=None, next_text=None):
        """Adds bottom navigation buttons side by side."""
        if back_text:
            back_btn = UIFactory.create_button(back_text, self.prev_stage.emit)
            self.nav_layout.addWidget(back_btn)

        # Spacer pushes Next button to the right
        self.nav_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        if next_text:
            next_btn = UIFactory.create_button(next_text, self.next_stage.emit)
            self.nav_layout.addWidget(next_btn)

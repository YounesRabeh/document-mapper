from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout

from core.manager.localization_manager import LocalizationManager
from gui.controllers import WorkflowStageState


class SidebarStageCard(QFrame):
    clicked = Signal(int)

    def __init__(self, stage_index: int, title_key: str, detail_key: str, localization: LocalizationManager):
        super().__init__()
        self.stage_index = stage_index
        self.title_key = title_key
        self.detail_key = detail_key
        self.localization = localization

        self.setObjectName("sidebarStageCard")
        self.setProperty("active", False)
        self.setProperty("completed", False)
        self.setProperty("blocked", False)
        self._blocked = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(82)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.index_label = QLabel()
        self.index_label.setObjectName("sidebarStageIndex")
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setFixedSize(34, 28)
        self.index_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(5)

        self.title_label = QLabel()
        self.title_label.setObjectName("sidebarStageTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.detail_label = QLabel()
        self.detail_label.setObjectName("sidebarStageDetail")
        self.detail_label.setWordWrap(True)
        self.detail_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.detail_label)

        layout.addWidget(self.index_label, alignment=Qt.AlignTop)
        layout.addLayout(text_layout, stretch=1)

        self.retranslate()

    def retranslate(self):
        self.index_label.setText(f"{self.stage_index:02d}")
        self.title_label.setText(self.localization.t(self.title_key))
        self.detail_label.setText(self.localization.t(self.detail_key))

    def set_stage_state(self, state: WorkflowStageState):
        self._blocked = state.blocked
        self.setProperty("active", state.active)
        self.setProperty("completed", state.completed)
        self.setProperty("blocked", state.blocked)
        self.setCursor(Qt.ArrowCursor if state.blocked else Qt.PointingHandCursor)
        for widget in (self, self.index_label, self.title_label, self.detail_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._blocked:
            self.clicked.emit(self.stage_index)
        super().mousePressEvent(event)

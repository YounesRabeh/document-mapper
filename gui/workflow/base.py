from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStringListModel, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QCompleter,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.certificate.models import ProjectSession
from core.manager.localization_manager import LocalizationManager
from gui.styles import apply_stylesheet

PAGE_MIN_WIDTH = 860
PAGE_MIN_HEIGHT = 560
PANEL_MIN_HEIGHT = 150
EDITOR_MIN_HEIGHT = 120
WIDE_PANEL_MIN_WIDTH = 420
SIDE_PANEL_MIN_WIDTH = 260


class TokenSuggestingLineEdit(QLineEdit):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._token_options: list[str] = []
        self._suspend_completion = False
        self.token_model = QStringListModel(self)
        self.token_completer = QCompleter(self.token_model, self)
        self.token_completer.setWidget(self)
        self.token_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.token_completer.setFilterMode(Qt.MatchContains)
        self.token_completer.setCompletionMode(QCompleter.PopupCompletion)
        self.token_completer.popup().setObjectName("tokenSuggestionPopup")
        self.token_completer.activated[str].connect(self.insert_token)
        self.textEdited.connect(self._update_token_popup)

    def set_token_options(self, options: list[str]):
        unique_options: list[str] = []
        seen: set[str] = set()
        for option in options:
            value = str(option or "").strip()
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            unique_options.append(value)
            seen.add(key)
        self._token_options = unique_options
        self.token_model.setStringList(unique_options)
        if not unique_options:
            self.token_completer.popup().hide()

    def available_tokens(self) -> list[str]:
        return list(self._token_options)

    def insert_token(self, token: str):
        token_value = str(token or "").strip()
        if not token_value:
            return
        token_range = self._current_token_range()
        if token_range is None:
            return

        open_index, cursor_position, _prefix = token_range
        suffix_start = cursor_position + 1 if cursor_position < len(self.text()) and self.text()[cursor_position] == "}" else cursor_position
        updated = f"{self.text()[:open_index]}{{{token_value}}}{self.text()[suffix_start:]}"

        self._suspend_completion = True
        try:
            self.setText(updated)
            self.setCursorPosition(open_index + len(token_value) + 2)
        finally:
            self._suspend_completion = False
        self.token_completer.popup().hide()

    def focusOutEvent(self, event):
        self.token_completer.popup().hide()
        super().focusOutEvent(event)

    def _current_token_range(self) -> tuple[int, int, str] | None:
        cursor_position = self.cursorPosition()
        text_before_cursor = self.text()[:cursor_position]
        open_index = text_before_cursor.rfind("{")
        if open_index < 0:
            return None

        token_prefix = text_before_cursor[open_index + 1 :]
        if "}" in token_prefix:
            return None
        return open_index, cursor_position, token_prefix

    def _update_token_popup(self, _text: str):
        if self._suspend_completion:
            return

        token_range = self._current_token_range()
        if token_range is None or not self._token_options:
            self.token_completer.popup().hide()
            return

        _open_index, _cursor_position, token_prefix = token_range
        self.token_completer.setCompletionPrefix(token_prefix)
        popup = self.token_completer.popup()
        popup.setCurrentIndex(self.token_completer.completionModel().index(0, 0))
        if self.token_completer.completionCount() <= 0:
            popup.hide()
            return

        popup_width = max(popup.sizeHintForColumn(0) + popup.verticalScrollBar().sizeHint().width() + 24, 240)
        completion_rect = self.cursorRect()
        completion_rect.setWidth(popup_width)
        self.token_completer.complete(completion_rect)


class WorkflowPage(QWidget):
    next_requested = Signal()
    prev_requested = Signal()
    session_changed = Signal()

    def __init__(self, localization: LocalizationManager, title_key: str, description_key: str):
        super().__init__()
        self.localization = localization
        self.session = ProjectSession()
        self._loading = False
        self._translation_bindings: list[tuple[object, str, str]] = []
        self.setMinimumSize(PAGE_MIN_WIDTH, PAGE_MIN_HEIGHT)
        self.setObjectName("workflowPage")
        apply_stylesheet(self, "workflow_page")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.scroll_content = QWidget()
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)

        scroll_layout = QVBoxLayout(self.scroll_content)
        scroll_layout.setContentsMargins(24, 16, 24, 16)
        scroll_layout.setSpacing(14)
        scroll_layout.setSizeConstraint(QVBoxLayout.SetMinAndMaxSize)

        self.title_label = QLabel()
        self.title_label.setObjectName("workflowTitle")
        self.title_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("workflowDescription")
        self.description_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self._bind_translation(self.title_label, "upper_text", title_key)
        self._bind_translation(self.description_label, "text", description_key)

        self.header_container = QWidget()
        self.header_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.header_layout = QVBoxLayout(self.header_container)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(6)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addWidget(self.description_label)

        scroll_layout.addWidget(self.header_container)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(16)
        self.body_layout.setAlignment(Qt.AlignTop)
        scroll_layout.addLayout(self.body_layout)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(24, 0, 24, 24)
        self.nav_layout.setSpacing(12)
        scroll_layout.addLayout(self.nav_layout)

        self.localization.language_changed.connect(self.retranslate_ui)

    def bind_session(self, session: ProjectSession):
        self.session = session
        self.refresh_from_session()
        self.scroll_to_top()

    def _create_card(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        card = QFrame()
        card.setObjectName("workflowCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(14)

        title_bar = QFrame()
        title_bar.setObjectName("workflowCardTitleBar")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        title_label = QLabel()
        title_label.setObjectName("workflowCardTitle")
        title_label.setWordWrap(False)
        title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self._bind_translation(title_label, "upper_text", title)
        title_layout.addWidget(title_label, 1)

        card_layout.addWidget(title_bar)
        return card, card_layout

    def _create_field_label(self, text: str) -> QLabel:
        label = QLabel()
        label.setObjectName("workflowFieldLabel")
        label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._bind_translation(label, "text", text)
        return label

    def refresh_from_session(self):
        pass

    def retranslate_page(self):
        pass

    def scroll_to_top(self):
        QTimer.singleShot(0, lambda: self.scroll_area.verticalScrollBar().setValue(0))

    def retranslate_ui(self, *_args):
        for widget, role, key in self._translation_bindings:
            self._apply_translation(widget, role, key)
        self.retranslate_page()

    def _bind_translation(self, widget: object, role: str, key: str):
        self._translation_bindings.append((widget, role, key))
        self._apply_translation(widget, role, key)

    def _apply_translation(self, widget: object, role: str, key: str):
        text = self.localization.t(key)
        if role == "text":
            widget.setText(text)
        elif role == "upper_text":
            widget.setText(text.upper())
        elif role == "title":
            widget.setTitle(text)
        elif role == "upper_title":
            widget.setTitle(text.upper())
        elif role == "placeholder":
            widget.setPlaceholderText(text)

    def _display_path(self, path: str) -> str:
        if not path:
            return self.localization.t("common.not_selected")
        return str(Path(path))

    def _display_file_name(self, path: str) -> str:
        if not path:
            return self.localization.t("common.not_selected")
        resolved = Path(path)
        return resolved.name or str(resolved)

    def _display_folder_name(self, path: str) -> str:
        if not path:
            return self.localization.t("common.not_selected")
        resolved = Path(path)
        return resolved.name or str(resolved)

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QSize, QStringListModel, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QCompleter,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import (
    CERTIFICATE_TYPE_OPTIONS,
    DEFAULT_CERTIFICATE_TYPE,
    DEFAULT_OUTPUT_NAMING_SCHEMA,
    DEFAULT_PLACEHOLDER_DELIMITER,
    GenerationResult,
    MappingEntry,
    ProjectSession,
    derive_placeholder_boundaries,
    normalize_certificate_type,
    normalize_placeholder_delimiter,
)
from core.certificate.template_service import TemplatePlaceholderService
from core.manager.localization_manager import LocalizationManager
from core.util.system_info import open_path
from gui.workflow.styles import MAPPING_TABLE_VIEWPORT_QSS, build_workflow_page_qss

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
        self.setStyleSheet(build_workflow_page_qss())

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
        scroll_layout.setContentsMargins(24, 24, 24, 16)
        scroll_layout.setSpacing(18)

        self.title_label = QLabel()
        self.title_label.setObjectName("workflowTitle")
        self.description_label = QLabel()
        self.description_label.setWordWrap(True)
        self.description_label.setObjectName("workflowDescription")
        self._bind_translation(self.title_label, "upper_text", title_key)
        self._bind_translation(self.description_label, "text", description_key)

        scroll_layout.addWidget(self.title_label)
        scroll_layout.addWidget(self.description_label)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(16)
        scroll_layout.addLayout(self.body_layout, stretch=1)
        scroll_layout.addStretch(1)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(24, 0, 24, 24)
        self.nav_layout.setSpacing(12)
        layout.addLayout(self.nav_layout)

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


class SetupPage(WorkflowPage):
    def __init__(self, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.setup.title",
            "page.setup.description",
        )

        form_card, form_card_layout = self._create_card("card.certificate_batch")
        form = QGridLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(16)
        form.setVerticalSpacing(12)
        form.setColumnMinimumWidth(0, 128)
        form.setColumnStretch(1, 1)
        form.setColumnMinimumWidth(2, 148)
        form_card_layout.addLayout(form)
        self.body_layout.addWidget(form_card)

        self.excel_input = self._create_browse_row(
            "button.workbook",
            "placeholder.select_excel_workbook",
            self._browse_excel,
        )
        self.template_input = self._create_browse_row(
            "button.template",
            "placeholder.select_word_template",
            self._browse_template,
        )
        self.output_input = self._create_browse_row(
            "button.output_folder",
            "placeholder.select_output_folder",
            self._browse_output_dir,
        )

        self._add_browse_row(form, 0, "field.excel_workbook", self.excel_input)
        self._add_browse_row(form, 1, "field.word_template", self.template_input)
        self._add_browse_row(form, 2, "field.output_folder", self.output_input)

        self.certificate_type_input = self._create_certificate_type_dropdown()
        self.certificate_type_input.setMinimumHeight(40)
        form.addWidget(self._create_field_label("field.certificate_type"), 3, 0)
        form.addWidget(self.certificate_type_input, 3, 1, 1, 2)

        self.certificate_type_hint = QLabel()
        self.certificate_type_hint.setWordWrap(True)
        self.certificate_type_hint.setObjectName("workflowHint")
        self._bind_translation(self.certificate_type_hint, "text", "hint.certificate_type")
        form.addWidget(self.certificate_type_hint, 4, 1, 1, 2)

        options_card, options_layout = self._create_card("card.export_options")

        self.export_pdf_checkbox = QCheckBox()
        self._bind_translation(self.export_pdf_checkbox, "text", "checkbox.export_pdf")
        self.pdf_timeout_input = QSpinBox()
        self.pdf_timeout_input.setRange(10, 3600)
        self.pdf_timeout_input.setSuffix(" s")
        self.pdf_timeout_input.setMinimumWidth(128)
        self.pdf_timeout_input.setMinimumHeight(40)

        export_row = QHBoxLayout()
        export_row.setContentsMargins(0, 0, 0, 0)
        export_row.setSpacing(12)

        export_row.addWidget(self.export_pdf_checkbox)
        export_row.addStretch()
        export_row.addWidget(self._create_field_label("field.pdf_timeout"))
        export_row.addWidget(self.pdf_timeout_input)
        options_layout.addLayout(export_row)
        self.body_layout.addWidget(options_card)

        status_card, status_card_layout = self._create_card("card.session_summary")
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setObjectName("workflowStatus")
        self.status_label.setMinimumHeight(72)
        status_card_layout.addWidget(self.status_label)
        self.body_layout.addWidget(status_card)

        self.next_button = QPushButton()
        self._bind_translation(self.next_button, "text", "button.next_mapping")
        self.next_button.setObjectName("workflowPrimaryButton")
        self.next_button.setMinimumWidth(170)
        self.next_button.setMinimumHeight(42)
        self.next_button.clicked.connect(self._go_next)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.next_button)

        self.certificate_type_input.currentTextChanged.connect(self._sync_session)
        self.export_pdf_checkbox.toggled.connect(self._sync_session)
        self.pdf_timeout_input.valueChanged.connect(self._sync_session)
        self.retranslate_ui()

    def _create_certificate_type_dropdown(self):
        widget = QComboBox()
        widget.setMinimumWidth(520)
        for option in CERTIFICATE_TYPE_OPTIONS:
            widget.addItem(option)
        return widget

    def _add_browse_row(self, grid: QGridLayout, row: int, label_text: str, row_widgets: dict):
        grid.addWidget(self._create_field_label(label_text), row, 0)
        grid.addWidget(row_widgets["container"], row, 1)
        grid.addWidget(row_widgets["button"], row, 2)
        grid.setRowMinimumHeight(row, 46)

    def _create_browse_row(self, button_key: str, placeholder_key: str, callback):
        container = QWidget()
        container.setMinimumWidth(420)
        container.setMinimumHeight(40)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        text_input = QLineEdit()
        self._bind_translation(text_input, "placeholder", placeholder_key)
        text_input.setClearButtonEnabled(True)
        text_input.setMinimumWidth(360)
        text_input.setMinimumHeight(40)
        browse_button = QPushButton()
        self._bind_translation(browse_button, "text", button_key)
        browse_button.setMinimumWidth(148)
        browse_button.setMinimumHeight(40)
        browse_button.clicked.connect(callback)

        text_input.textChanged.connect(self._sync_session)
        layout.addWidget(text_input, stretch=1)

        return {
            "container": container,
            "input": text_input,
            "button": browse_button,
        }

    def refresh_from_session(self):
        self._loading = True
        try:
            self.excel_input["input"].setText(self.session.excel_path)
            self.template_input["input"].setText(self.session.template_path)
            self.output_input["input"].setText(self.session.output_dir)
            self._ensure_certificate_type_option(self.session.certificate_type)
            current_certificate_type = self.session.certificate_type or DEFAULT_CERTIFICATE_TYPE
            self.certificate_type_input.setCurrentText(current_certificate_type)
            self.export_pdf_checkbox.setChecked(self.session.export_pdf)
            self.pdf_timeout_input.setValue(self.session.pdf_timeout_seconds)
        finally:
            self._loading = False
        self._refresh_status()

    def _refresh_status(self):
        lines = [
            self.localization.t("summary.workbook", value=self._display_path(self.session.excel_path)),
            self.localization.t("summary.template", value=self._display_path(self.session.template_path)),
            self.localization.t("summary.output_folder", value=self._display_path(self.session.output_dir)),
            self.localization.t(
                "summary.certificate_type",
                value=self.session.certificate_type or DEFAULT_CERTIFICATE_TYPE,
            ),
            self.localization.t("summary.mappings_configured", count=len(self.session.mappings)),
        ]
        self.status_label.setText("\n".join(lines))

    def _sync_session(self, *_args):
        if self._loading:
            return

        self.session.excel_path = self.excel_input["input"].text().strip()
        self.session.template_path = self.template_input["input"].text().strip()
        self.session.output_dir = self.output_input["input"].text().strip()
        self.session.certificate_type = self.certificate_type_input.currentText().strip() or DEFAULT_CERTIFICATE_TYPE
        self.session.export_pdf = self.export_pdf_checkbox.isChecked()
        self.session.pdf_timeout_seconds = self.pdf_timeout_input.value()
        self._refresh_status()
        self.session_changed.emit()

    def _ensure_certificate_type_option(self, value: str):
        normalized = normalize_certificate_type(value)
        if not normalized:
            return
        if self.certificate_type_input.findText(normalized) == -1:
            self.certificate_type_input.addItem(normalized)

    def _set_text_and_sync(self, widget: QLineEdit, value: str):
        widget.setText(value)
        self._sync_session()

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.localization.t("dialog.select_excel_workbook.title"),
            "",
            self.localization.t("dialog.excel_files"),
        )
        if path:
            self._set_text_and_sync(self.excel_input["input"], path)

    def _browse_template(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.localization.t("dialog.select_word_template.title"),
            "",
            self.localization.t("dialog.word_files"),
        )
        if path:
            self._set_text_and_sync(self.template_input["input"], path)

    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(
            self,
            self.localization.t("dialog.select_output_folder.title"),
            self.session.output_dir or "",
        )
        if path:
            self._set_text_and_sync(self.output_input["input"], path)

    def _go_next(self):
        self._sync_session()
        self.next_requested.emit()

    def retranslate_page(self):
        self._refresh_status()


class MappingPage(WorkflowPage):
    def __init__(
        self,
        excel_service: ExcelDataService,
        generator: CertificateGenerator,
        localization: LocalizationManager,
        template_service: TemplatePlaceholderService | None = None,
    ):
        super().__init__(
            localization,
            "page.mapping.title",
            "page.mapping.description",
        )
        self.excel_service = excel_service
        self.generator = generator
        self.template_service = template_service or TemplatePlaceholderService()
        self.columns: list[str] = []
        self.detected_placeholders: list[str] = []
        self._last_detected_delimiters: tuple[str, str] | None = None
        self._delimiter_refresh_timer = QTimer(self)
        self._delimiter_refresh_timer.setSingleShot(True)
        self._delimiter_refresh_timer.setInterval(180)
        self._delimiter_refresh_timer.timeout.connect(self._auto_refresh_mapping_context)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        self.body_layout.addLayout(content_layout, stretch=1)

        self.left_box, left_layout = self._create_card("group.workbook_columns")
        self.left_box.setMinimumWidth(SIDE_PANEL_MIN_WIDTH)
        self.left_box.setMinimumHeight(PANEL_MIN_HEIGHT + 80)
        self.columns_label = QLabel()
        self.columns_label.setWordWrap(True)
        self.columns_label.setObjectName("workflowStatus")
        self.columns_hint = QLabel()
        self.columns_hint.setWordWrap(True)
        self.columns_hint.setObjectName("workflowHint")
        self._bind_translation(self.columns_hint, "text", "hint.columns_panel")
        self.columns_list = QListWidget()
        self.columns_list.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.columns_list.setAlternatingRowColors(False)
        self.columns_list.setSpacing(2)
        self.columns_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.columns_list.setFocusPolicy(Qt.NoFocus)
        left_layout.addWidget(self.columns_label)
        left_layout.addWidget(self.columns_hint)
        left_layout.addWidget(self.columns_list)
        content_layout.addWidget(self.left_box, stretch=1)

        self.right_box, right_layout = self._create_card("group.placeholder_mappings")
        self.right_box.setMinimumWidth(WIDE_PANEL_MIN_WIDTH)
        self.mapping_hint = QLabel()
        self.mapping_hint.setWordWrap(True)
        self.mapping_hint.setObjectName("workflowHint")
        delimiter_row = QHBoxLayout()
        delimiter_row.setContentsMargins(0, 0, 0, 0)
        delimiter_row.setSpacing(12)
        self.delimiter_label = self._create_field_label("field.placeholder_delimiter")
        self.delimiter_input = QLineEdit()
        self.delimiter_input.setClearButtonEnabled(True)
        self.delimiter_input.setMaximumWidth(220)
        self.delimiter_input.setMinimumHeight(40)
        self.delimiter_input.textChanged.connect(self._sync_delimiter)
        delimiter_row.addWidget(self.delimiter_label)
        delimiter_row.addWidget(self.delimiter_input)
        delimiter_row.addStretch()
        self.template_status = QLabel()
        self.template_status.setWordWrap(True)
        self.template_status.setObjectName("workflowStatus")

        self.output_naming_group = QGroupBox()
        self._bind_translation(self.output_naming_group, "upper_title", "group.output_naming_schema")
        output_naming_layout = QGridLayout(self.output_naming_group)
        output_naming_layout.setContentsMargins(16, 18, 16, 16)
        output_naming_layout.setHorizontalSpacing(12)
        output_naming_layout.setVerticalSpacing(10)
        output_naming_layout.setColumnMinimumWidth(0, 128)
        output_naming_layout.setColumnStretch(1, 1)
        self.output_naming_schema_label = self._create_field_label("field.output_naming_schema")
        self.output_naming_schema_input = TokenSuggestingLineEdit()
        self.output_naming_schema_input.setClearButtonEnabled(True)
        self.output_naming_schema_input.setMinimumHeight(40)
        self.output_naming_schema_input.setPlaceholderText(DEFAULT_OUTPUT_NAMING_SCHEMA)
        self.output_naming_schema_input.textChanged.connect(self._sync_output_naming_schema)
        self.output_naming_schema_hint = QLabel()
        self.output_naming_schema_hint.setWordWrap(True)
        self.output_naming_schema_hint.setObjectName("workflowHint")
        self._bind_translation(self.output_naming_schema_hint, "text", "hint.output_naming_schema")
        output_naming_layout.addWidget(self.output_naming_schema_label, 0, 0)
        output_naming_layout.addWidget(self.output_naming_schema_input, 0, 1)
        output_naming_layout.addWidget(self.output_naming_schema_hint, 1, 1)

        self.mapping_table = QTableWidget(0, 2)
        self.mapping_table.setObjectName("mappingTable")
        self.mapping_table.setAlternatingRowColors(False)
        self.mapping_table.setShowGrid(False)
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mapping_table.verticalHeader().setVisible(False)
        self.mapping_table.verticalHeader().setDefaultSectionSize(44)
        self.mapping_table.setColumnWidth(0, 280)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mapping_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mapping_table.setMinimumHeight(300)
        self.mapping_table.viewport().setStyleSheet(MAPPING_TABLE_VIEWPORT_QSS)
        self.mapping_table.itemSelectionChanged.connect(self._update_actions)

        mapping_buttons = QHBoxLayout()
        self.add_button = QPushButton()
        self.refresh_button = QPushButton()
        self._bind_translation(self.add_button, "text", "button.add_mapping")
        self._bind_translation(self.refresh_button, "text", "button.refresh_mapping_data")
        self.add_button.clicked.connect(self._add_empty_mapping_row)
        self.refresh_button.clicked.connect(self._refresh_mapping_context)
        mapping_buttons.addWidget(self.add_button)
        mapping_buttons.addWidget(self.refresh_button)
        mapping_buttons.addStretch()

        self.validation_summary = QLabel()
        self.validation_summary.setWordWrap(True)
        self.validation_summary.setObjectName("workflowStatus")
        self.validation_output = QPlainTextEdit()
        self.validation_output.setReadOnly(True)
        self.validation_output.setMaximumBlockCount(200)
        self.validation_output.setMinimumHeight(160)
        self.validation_label = self._create_field_label("label.validation")

        right_layout.addWidget(self.mapping_hint)
        right_layout.addLayout(delimiter_row)
        right_layout.addWidget(self.template_status)
        right_layout.addWidget(self.output_naming_group)
        right_layout.addLayout(mapping_buttons)
        right_layout.addWidget(self.mapping_table, stretch=1)
        right_layout.addWidget(self.validation_label)
        right_layout.addWidget(self.validation_summary)
        right_layout.addWidget(self.validation_output)
        content_layout.addWidget(self.right_box, stretch=2)

        self.back_button = QPushButton()
        self.next_button = QPushButton()
        self._bind_translation(self.back_button, "text", "button.back")
        self._bind_translation(self.next_button, "text", "button.next_generate")
        self.next_button.setObjectName("workflowPrimaryButton")
        self.back_button.clicked.connect(self.prev_requested.emit)
        self.next_button.clicked.connect(self._go_next)
        self.nav_layout.addWidget(self.back_button)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.next_button)
        self.retranslate_ui()

    def refresh_from_session(self):
        self._loading = True
        try:
            self.delimiter_input.setText(self.session.placeholder_delimiter)
            self.output_naming_schema_input.setText(self.session.output_naming_schema)
        finally:
            self._loading = False
        self._last_detected_delimiters = (
            derive_placeholder_boundaries(self.session.detected_placeholder_delimiter)
            if self.session.detected_placeholder_delimiter
            else None
        )
        self._refresh_mapping_help_text()
        self._reload_mapping_context()

    def _current_delimiter(self) -> str:
        return self.delimiter_input.text().strip()

    def _placeholder_example(self) -> str:
        delimiter = self._current_delimiter() or DEFAULT_PLACEHOLDER_DELIMITER
        start, end = derive_placeholder_boundaries(delimiter)
        return f"{start}NOME{end}"

    def _placeholder_pair_label(self) -> str:
        delimiter = self._current_delimiter() or DEFAULT_PLACEHOLDER_DELIMITER
        start, end = derive_placeholder_boundaries(delimiter)
        return f"{start}...{end}"

    def _refresh_mapping_help_text(self):
        self.mapping_hint.setText(
            self.localization.t(
                "hint.mapping_editor",
                example=self._placeholder_example(),
            )
        )

    def _update_template_status(self):
        delimiter = self._current_delimiter()
        if not self.session.template_path:
            self.template_status.setText(
                self.localization.t(
                    "status.select_template_for_placeholders",
                    example=self._placeholder_example(),
                )
            )
            return
        if not delimiter:
            self.template_status.setText(self.localization.t("status.placeholder_delimiter_required"))
            return
        if self._last_detected_delimiters == derive_placeholder_boundaries(delimiter):
            if self.detected_placeholders:
                self.template_status.setText(
                    self.localization.t(
                        "status.detected_template_placeholders",
                        count=len(self.detected_placeholders),
                    )
                )
            else:
                self.template_status.setText(
                    self.localization.t(
                        "status.no_template_placeholders_detected",
                        example=self._placeholder_pair_label(),
                    )
                )
            return
        self.template_status.setText(
            self.localization.t(
                "status.refresh_to_detect_placeholders",
                example=self._placeholder_example(),
            )
        )

    def _load_columns(self):
        self.columns = []
        self.columns_list.clear()
        if not self.session.excel_path:
            self.columns_label.setText(self.localization.t("status.select_workbook_for_columns"))
            self._refresh_output_naming_tokens()
            return

        try:
            preview = self.excel_service.inspect(self.session.excel_path)
        except Exception as exc:
            self.columns_label.setText(self.localization.t("status.could_not_inspect_workbook", error=exc))
            self._refresh_output_naming_tokens()
            return

        self.columns = preview.columns
        self.columns_label.setText(
            self.localization.t(
                "status.rows_detected",
                row_count=preview.row_count,
                path=self._display_file_name(self.session.excel_path),
            )
        )
        for column in self.columns:
            self._add_column_entry(column)
        self._refresh_output_naming_tokens()

    def _output_naming_tokens(self) -> list[str]:
        tokens = list(self.columns)
        tokens.extend(["ROW", "CERTIFICATE_TYPE"])
        return tokens

    def _refresh_output_naming_tokens(self):
        self.output_naming_schema_input.set_token_options(self._output_naming_tokens())

    def _sync_output_naming_schema(self, *_args):
        if self._loading:
            return

        self.session.output_naming_schema = self.output_naming_schema_input.text().strip()
        self._refresh_validation()
        self.session_changed.emit()

    def _add_column_entry(self, column_name: str):
        item = QListWidgetItem()
        item.setFlags(Qt.NoItemFlags)
        self.columns_list.addItem(item)

        row_widget = QFrame()
        row_widget.setObjectName("columnEntry")
        row_widget.setMinimumHeight(44)
        layout = QHBoxLayout(row_widget)
        layout.setContentsMargins(14, 8, 10, 8)
        layout.setSpacing(10)

        label = QLabel(column_name)
        label.setObjectName("columnEntryLabel")
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        button = QPushButton("→")
        button.setObjectName("columnEntryAddButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedSize(28, 28)
        button.clicked.connect(lambda _checked=False, value=column_name: self._assign_column_to_mapping(value))

        layout.addWidget(label, stretch=1)
        layout.addWidget(button, alignment=Qt.AlignRight | Qt.AlignVCenter)
        item.setSizeHint(QSize(0, 48))
        self.columns_list.setItemWidget(item, row_widget)

    def _populate_table(self):
        self.mapping_table.setRowCount(0)
        mappings = self._build_mapping_rows()
        for mapping in mappings:
            self._add_mapping_row(mapping.placeholder, mapping.column_name)

    def _build_mapping_rows(self) -> list[MappingEntry]:
        merged_mappings: list[MappingEntry] = []
        detected_lookup = {placeholder: None for placeholder in self.detected_placeholders}
        manual_mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in self.session.mappings
        ]

        for placeholder in self.detected_placeholders:
            matching = next((entry for entry in manual_mappings if entry.placeholder == placeholder), None)
            if matching is not None:
                merged_mappings.append(matching)
            else:
                merged_mappings.append(MappingEntry(placeholder=placeholder))

        for entry in manual_mappings:
            placeholder = entry.placeholder.strip()
            if not placeholder or placeholder not in detected_lookup:
                merged_mappings.append(entry)

        if not merged_mappings:
            return [MappingEntry()]

        self.session.mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in merged_mappings
            if entry.placeholder or entry.column_name
        ]
        return merged_mappings

    def _load_template_placeholders(self):
        self.detected_placeholders = []
        delimiter = self._current_delimiter()
        if not self.session.template_path or not delimiter:
            self._last_detected_delimiters = None
            self.session.detected_placeholder_delimiter = ""
            self.session.detected_placeholder_count = 0
            self._update_template_status()
            return

        try:
            placeholders = self.template_service.extract_placeholders(self.session.template_path, delimiter)
        except Exception as exc:
            self._last_detected_delimiters = None
            self.session.detected_placeholder_delimiter = ""
            self.session.detected_placeholder_count = 0
            self.template_status.setText(
                self.localization.t("status.could_not_inspect_template", error=exc)
            )
            return

        self.detected_placeholders = placeholders
        self._last_detected_delimiters = derive_placeholder_boundaries(delimiter)
        self.session.detected_placeholder_delimiter = delimiter
        self.session.detected_placeholder_count = len(placeholders)
        if placeholders:
            self.template_status.setText(
                self.localization.t(
                    "status.detected_template_placeholders",
                    count=len(placeholders),
                )
            )
            return

        self.template_status.setText(
            self.localization.t(
                "status.no_template_placeholders_detected",
                example=self._placeholder_pair_label(),
            )
        )

    def _reload_mapping_context(self, previous_detected_placeholders: set[str] | None = None):
        self._loading = True
        try:
            self._load_columns()
            self._load_template_placeholders()
            self._prune_stale_detected_mappings(previous_detected_placeholders or set())
            self._populate_table()
            self._refresh_validation()
        finally:
            self._loading = False
        self._update_actions()

    def _refresh_mapping_context(self):
        self._delimiter_refresh_timer.stop()
        self._sync_session_from_table(emit_signal=False)
        previous_detected_placeholders = set(self.detected_placeholders)
        if self.session.excel_path:
            self.excel_service.clear_cache(self.session.excel_path)
        else:
            self.excel_service.clear_cache()
        if self.session.template_path:
            self.template_service.clear_cache(self.session.template_path)
        else:
            self.template_service.clear_cache()
        self._reload_mapping_context(previous_detected_placeholders)
        self.session_changed.emit()

    def _auto_refresh_mapping_context(self):
        self._sync_session_from_table(emit_signal=False)
        previous_detected_placeholders = set(self.detected_placeholders)
        self._reload_mapping_context(previous_detected_placeholders)
        self.session_changed.emit()

    def _prune_stale_detected_mappings(self, previous_detected_placeholders: set[str]):
        if not previous_detected_placeholders:
            return

        stale_placeholders = previous_detected_placeholders.difference(self.detected_placeholders)
        if not stale_placeholders:
            return

        self.session.mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in self.session.mappings
            if entry.placeholder.strip() not in stale_placeholders
        ]

    def _sync_delimiter(self, *_args):
        if self._loading:
            return

        normalized_delimiter = normalize_placeholder_delimiter(self.delimiter_input.text())
        if normalized_delimiter != self.delimiter_input.text():
            cursor_position = min(self.delimiter_input.cursorPosition(), len(normalized_delimiter))
            self._loading = True
            try:
                self.delimiter_input.setText(normalized_delimiter)
                self.delimiter_input.setCursorPosition(cursor_position)
            finally:
                self._loading = False

        self.session.placeholder_delimiter = normalized_delimiter
        self.session.detected_placeholder_delimiter = ""
        self.session.detected_placeholder_count = 0
        self._last_detected_delimiters = None
        self._refresh_mapping_help_text()
        if not self.session.template_path or not normalized_delimiter:
            self._refresh_mapping_context()
            return

        self.template_status.setText(self.localization.t("status.detecting_placeholders"))
        self._refresh_validation()
        self._update_actions()
        self.session_changed.emit()
        self._delimiter_refresh_timer.start()

    def _add_empty_mapping_row(self):
        row = self._add_mapping_row()
        self.mapping_table.setCurrentCell(row, 0)
        self.mapping_table.scrollToBottom()
        placeholder_combo = self._get_cell_editor(row, 0, QComboBox)
        if isinstance(placeholder_combo, QComboBox):
            if placeholder_combo.lineEdit() is not None:
                placeholder_combo.lineEdit().setFocus()
            else:
                placeholder_combo.setFocus()

    def _add_mapping_row(self, placeholder: str = "", column_name: str = ""):
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)
        self.mapping_table.setRowHeight(row, 52)

        placeholder_item = QTableWidgetItem("")
        placeholder_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.mapping_table.setItem(row, 0, placeholder_item)
        column_item = QTableWidgetItem("")
        column_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.mapping_table.setItem(row, 1, column_item)

        placeholder_combo = self._create_placeholder_dropdown(placeholder)
        self.mapping_table.setCellWidget(row, 0, self._wrap_table_editor(placeholder_combo))

        combo = QComboBox()
        combo.addItem("")
        combo.addItems(self.columns)
        combo.setMinimumHeight(34)
        if column_name:
            combo.setCurrentText(column_name)
        combo.currentTextChanged.connect(self._sync_session_from_table)
        combo.installEventFilter(self)
        self.mapping_table.setCellWidget(row, 1, self._wrap_table_editor(combo, self._create_row_delete_button()))
        self._update_actions()
        return row

    def _wrap_table_editor(self, editor: QWidget, trailing_widget: QWidget | None = None) -> QWidget:
        container = QWidget()
        container.setObjectName("mappingCellContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)
        layout.addWidget(editor, 1)
        if trailing_widget is not None:
            layout.addWidget(trailing_widget, 0, Qt.AlignRight | Qt.AlignVCenter)
        return container

    def _create_placeholder_dropdown(self, placeholder: str) -> QComboBox:
        combo = QComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMinimumHeight(34)
        combo.addItem("")
        for value in self.detected_placeholders:
            if combo.findText(value) == -1:
                combo.addItem(value)
        if placeholder and combo.findText(placeholder) == -1:
            combo.addItem(placeholder)
        combo.setCurrentText(placeholder)
        combo.currentTextChanged.connect(self._sync_session_from_table)
        combo.installEventFilter(self)
        if combo.lineEdit() is not None:
            combo.lineEdit().installEventFilter(self)
        return combo

    def _get_cell_editor(self, row: int, column: int, editor_type):
        cell_widget = self.mapping_table.cellWidget(row, column)
        if isinstance(cell_widget, editor_type):
            return cell_widget
        if isinstance(cell_widget, QWidget):
            return cell_widget.findChild(editor_type)
        return None

    def _create_row_delete_button(self) -> QPushButton:
        button = QPushButton("×")
        button.setObjectName("mappingRowDeleteButton")
        button.setCursor(Qt.PointingHandCursor)
        button.setFixedSize(30, 30)
        button.clicked.connect(lambda: self._remove_row_for_widget(button))
        return button

    def _find_row_for_widget(self, widget: QWidget) -> int:
        for row in range(self.mapping_table.rowCount()):
            for column in range(self.mapping_table.columnCount()):
                cell_widget = self.mapping_table.cellWidget(row, column)
                if cell_widget is widget:
                    return row
                if isinstance(cell_widget, QWidget) and cell_widget.findChild(type(widget)) is widget:
                    return row
        return -1

    def _remove_selected_row(self):
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)
            self._sync_session_from_table()
        self._update_actions()

    def _remove_row_for_widget(self, widget: QWidget):
        row = self._find_row_for_widget(widget)
        if row < 0:
            return
        self.mapping_table.setCurrentCell(row, 0)
        self.mapping_table.removeRow(row)
        self._sync_session_from_table()
        self._update_actions()

    def _assign_column_to_mapping(self, column_name: str):
        row = self.mapping_table.currentRow()
        if row < 0 or row >= self.mapping_table.rowCount():
            row = self._add_mapping_row(column_name=column_name)
            self.mapping_table.setCurrentCell(row, 0)
            return

        combo = self._get_cell_editor(row, 1, QComboBox)
        if isinstance(combo, QComboBox):
            combo.setCurrentText(column_name)
        self.mapping_table.setCurrentCell(row, 0)

    def _sync_session_from_table(self, *_args, emit_signal: bool = True):
        if self._loading:
            return

        mappings: list[MappingEntry] = []
        for row in range(self.mapping_table.rowCount()):
            placeholder_widget = self._get_cell_editor(row, 0, QComboBox)
            placeholder = placeholder_widget.currentText().strip() if isinstance(placeholder_widget, QComboBox) else ""
            combo = self._get_cell_editor(row, 1, QComboBox)
            column_name = combo.currentText().strip() if isinstance(combo, QComboBox) else ""

            if placeholder or column_name:
                mappings.append(MappingEntry(placeholder=placeholder, column_name=column_name))

        self.session.mappings = mappings
        self._refresh_validation()
        self._update_actions()
        if emit_signal:
            self.session_changed.emit()

    def _refresh_validation(self):
        errors = self.generator.validate_session(self.session)
        if errors:
            translated = [self.localization.translate_runtime_text(error) for error in errors]
            self.validation_summary.setText(
                self.localization.t("status.validation_issues", count=len(translated))
            )
            self.validation_output.setPlainText("\n".join(f"- {error}" for error in translated))
        else:
            ready_text = self.localization.t("status.ready_to_generate")
            self.validation_summary.setText(ready_text)
            self.validation_output.setPlainText(self.localization.t("status.validation_ready_detail"))

    def _go_next(self):
        self._sync_session_from_table()
        errors = self.generator.validate_session(self.session)
        if errors:
            translated = [self.localization.translate_runtime_text(error) for error in errors]
            QMessageBox.warning(self, self.localization.t("dialog.cannot_continue.title"), "\n".join(translated))
            return
        self.next_requested.emit()

    def retranslate_page(self):
        self.columns_label.setText(self.localization.t("status.no_workbook_loaded"))
        self._refresh_mapping_help_text()
        self.mapping_table.setHorizontalHeaderLabels(
            [
                self.localization.t("table.placeholder"),
                self.localization.t("table.excel_column"),
            ]
        )
        self._load_template_placeholders()
        self._refresh_validation()
        if self.session.excel_path:
            self._load_columns()
        self._update_actions()

    def _update_actions(self, *_args):
        return None

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.FocusIn, QEvent.MouseButtonPress):
            self._select_row_for_editor(watched)
        return super().eventFilter(watched, event)

    def _select_row_for_editor(self, editor):
        for row in range(self.mapping_table.rowCount()):
            for column in range(self.mapping_table.columnCount()):
                cell_widget = self.mapping_table.cellWidget(row, column)
                if cell_widget is editor:
                    self.mapping_table.setCurrentCell(row, column)
                    return
                if isinstance(cell_widget, QWidget) and cell_widget.findChild(type(editor)) is editor:
                    self.mapping_table.setCurrentCell(row, column)
                    return


class GenerationWorker(QObject):
    log_message = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, generator: CertificateGenerator, session: ProjectSession):
        super().__init__()
        self.generator = generator
        self.session = session

    def run(self):
        try:
            result = self.generator.generate(self.session, progress_callback=self.log_message.emit)
        except Exception as exc:
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


class GeneratePage(WorkflowPage):
    results_ready = Signal(object)

    def __init__(self, generator: CertificateGenerator, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.generate.title",
            "page.generate.description",
        )
        self.generator = generator
        self._thread: QThread | None = None
        self._worker: GenerationWorker | None = None

        self.summary_box, summary_layout = self._create_card("group.batch_summary")
        self.summary_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.summary_output = QLabel()
        self.summary_output.setObjectName("workflowInfoBox")
        self.summary_output.setWordWrap(True)
        self.summary_output.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.summary_output.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.summary_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.summary_output.setMinimumHeight(0)
        summary_layout.addWidget(self.summary_output)
        self.body_layout.addWidget(self.summary_box)

        self.log_box, log_layout = self._create_card("group.generation_log")
        self.log_box.setMinimumHeight(PANEL_MIN_HEIGHT + 80)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        log_layout.addWidget(self.log_output)
        self.body_layout.addWidget(self.log_box, stretch=1)

        self.back_button = QPushButton()
        self.generate_button = QPushButton()
        self._bind_translation(self.back_button, "text", "button.back")
        self._bind_translation(self.generate_button, "text", "button.generate_certificates")
        self.back_button.clicked.connect(self.prev_requested.emit)
        self.generate_button.clicked.connect(self._start_generation)
        self.nav_layout.addWidget(self.back_button)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.generate_button)
        self.retranslate_ui()

    def refresh_from_session(self):
        errors = self.generator.validate_session(self.session)
        summary_lines = [
            self.localization.t("summary.workbook", value=self._display_path(self.session.excel_path)),
            self.localization.t("summary.template", value=self._display_path(self.session.template_path)),
            self.localization.t("summary.output", value=self._display_path(self.session.output_dir)),
            self.localization.t(
                "summary.output_naming_schema",
                value=self.session.output_naming_schema or DEFAULT_OUTPUT_NAMING_SCHEMA,
            ),
            self.localization.t("summary.mappings", count=len(self.session.mappings)),
            self.localization.t(
                "summary.export_pdf_enabled",
                value=self.localization.t("common.yes") if self.session.export_pdf else self.localization.t("common.no"),
            ),
            "",
            self.localization.t("summary.validation"),
        ]
        if errors:
            summary_lines.extend(f"- {self.localization.translate_runtime_text(error)}" for error in errors)
        else:
            summary_lines.append(self.localization.t("summary.ready_to_generate_short"))
        self.summary_output.setText("\n".join(summary_lines))

    def _start_generation(self):
        errors = self.generator.validate_session(self.session)
        if errors:
            translated = [self.localization.translate_runtime_text(error) for error in errors]
            QMessageBox.warning(self, self.localization.t("dialog.cannot_generate.title"), "\n".join(translated))
            self.refresh_from_session()
            return

        if self._thread is not None:
            return

        self.log_output.clear()
        self.generate_button.setEnabled(False)
        session_copy = self.session.clone()

        self._thread = QThread(self)
        self._worker = GenerationWorker(self.generator, session_copy)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_message.connect(self.log_output.appendPlainText)
        self._worker.finished.connect(self._handle_finished)
        self._worker.failed.connect(self._handle_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()

    def _handle_finished(self, result: GenerationResult):
        self.log_output.appendPlainText(self.localization.t("log.generation_finished"))
        self.generate_button.setEnabled(True)
        self.results_ready.emit(result)
        self._cleanup_thread()

    def _handle_failed(self, error_message: str):
        self.log_output.appendPlainText(
            self.localization.t("log.generation_failed", error=self.localization.translate_runtime_text(error_message))
        )
        self.generate_button.setEnabled(True)
        QMessageBox.critical(
            self,
            self.localization.t("dialog.generation_failed.title"),
            self.localization.translate_runtime_text(error_message),
        )
        self._cleanup_thread()

    def _cleanup_thread(self):
        if self._worker is not None:
            self._worker.deleteLater()
        self._worker = None
        self._thread = None

    def retranslate_page(self):
        self.refresh_from_session()


class ResultsPage(WorkflowPage):
    def __init__(self, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.results.title",
            "page.results.description",
        )
        self.result = GenerationResult()

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        self.summary_label.setMinimumHeight(72)
        self.body_layout.addWidget(self.summary_label)

        self.files_box = QGroupBox()
        self._bind_translation(self.files_box, "upper_title", "group.generated_files")
        files_layout = QVBoxLayout(self.files_box)
        files_layout.setContentsMargins(12, 12, 12, 12)
        self.files_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(PANEL_MIN_HEIGHT)
        self.files_list.itemDoubleClicked.connect(self._open_selected_item)
        files_layout.addWidget(self.files_list)
        self.body_layout.addWidget(self.files_box, stretch=1)

        self.errors_box = QGroupBox()
        self._bind_translation(self.errors_box, "upper_title", "group.errors")
        errors_layout = QVBoxLayout(self.errors_box)
        errors_layout.setContentsMargins(12, 12, 12, 12)
        self.errors_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.errors_output = QPlainTextEdit()
        self.errors_output.setReadOnly(True)
        self.errors_output.setMinimumHeight(PANEL_MIN_HEIGHT)
        errors_layout.addWidget(self.errors_output)
        self.body_layout.addWidget(self.errors_box, stretch=1)

        self.back_button = QPushButton()
        self.open_output_button = QPushButton()
        self.open_log_button = QPushButton()
        self._bind_translation(self.back_button, "text", "button.back")
        self._bind_translation(self.open_output_button, "text", "button.open_output_folder")
        self._bind_translation(self.open_log_button, "text", "button.open_log")
        self.back_button.clicked.connect(self.prev_requested.emit)
        self.open_output_button.clicked.connect(self._open_output_folder)
        self.open_log_button.clicked.connect(self._open_log)

        self.nav_layout.addWidget(self.back_button)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.open_log_button)
        self.nav_layout.addWidget(self.open_output_button)
        self.retranslate_ui()

    def bind_result(self, result: GenerationResult, session: ProjectSession):
        self.result = result
        self.session = session
        self.refresh_from_session()

    def refresh_from_session(self):
        if not self.result.total_rows and not self.result.generated_docx_paths and not self.result.generated_pdf_paths:
            self.summary_label.setText(self.localization.t("status.no_generation_results"))
        else:
            total_files = len(self.result.generated_docx_paths) + len(self.result.generated_pdf_paths)
            summary_lines = [
                self.localization.t(
                    "results.created_docx",
                    success_count=self.result.success_count,
                    total_rows=self.result.total_rows,
                ),
                self.localization.t("results.generated_pdfs", count=len(self.result.generated_pdf_paths)),
                self.localization.t("results.files_listed", count=total_files),
            ]
            if self.result.last_certificate_number:
                summary_lines.append(
                    self.localization.t("results.last_certificate_number", value=self.result.last_certificate_number)
                )
            if self.result.log_path:
                summary_lines.append(self.localization.t("results.log_file", path=self.result.log_path))
            self.summary_label.setText("\n".join(summary_lines))

        self.files_list.clear()
        for path in [*self.result.generated_docx_paths, *self.result.generated_pdf_paths]:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.UserRole, path)
            self.files_list.addItem(item)

        if self.result.errors:
            translated = [self.localization.translate_runtime_text(error) for error in self.result.errors]
            self.errors_output.setPlainText("\n".join(translated))
        else:
            self.errors_output.setPlainText(self.localization.t("results.no_generation_errors"))

    def _open_selected_item(self, item: QListWidgetItem):
        path = item.data(Qt.UserRole)
        if path:
            open_path(path)

    def _open_output_folder(self):
        if self.session.output_dir:
            open_path(self.session.output_dir)

    def _open_log(self):
        if self.result.log_path:
            open_path(self.result.log_path)

    def retranslate_page(self):
        self.refresh_from_session()

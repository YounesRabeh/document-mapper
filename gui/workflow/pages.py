from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEvent, QObject, QThread, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
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
    GenerationResult,
    MappingEntry,
    ProjectSession,
    normalize_certificate_type,
)
from core.manager.localization_manager import LocalizationManager
from core.util.system_info import open_path

PAGE_MIN_WIDTH = 860
PAGE_MIN_HEIGHT = 560
PANEL_MIN_HEIGHT = 150
EDITOR_MIN_HEIGHT = 120
WIDE_PANEL_MIN_WIDTH = 420
SIDE_PANEL_MIN_WIDTH = 260
WORKFLOW_PAGE_QSS = """
QWidget#workflowPage {
    background: palette(window);
}

QScrollArea {
    background: transparent;
    border: none;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QLabel#workflowTitle {
    color: palette(window-text);
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 0.2px;
    margin-bottom: 2px;
}

QLabel#workflowDescription {
    color: palette(window-text);
    font-size: 14px;
    line-height: 1.45;
}

QFrame#workflowCard,
QGroupBox {
    background: palette(alternate-base);
    border: 1px solid palette(midlight);
    border-radius: 14px;
}

QFrame#workflowCardTitleBar {
    background: transparent;
    border: none;
}

QLabel#workflowCardTitle {
    color: palette(window-text);
    font-size: 15px;
    font-weight: 800;
    line-height: 1.3;
}

QLabel#workflowHint {
    color: palette(window-text);
    font-size: 13px;
}

QLabel#workflowFieldLabel {
    color: palette(text);
    font-size: 14px;
    font-weight: 500;
}

QLabel#workflowStatus {
    color: palette(window-text);
    font-size: 13px;
    line-height: 1.4;
}

QLabel#workflowInfoBox {
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 10px;
    color: palette(text);
    padding: 12px 14px;
    line-height: 1.45;
}

QGroupBox {
    margin-top: 0;
    padding-top: 30px;
    color: palette(window-text);
    font-weight: 700;
}

QGroupBox::title {
    subcontrol-origin: padding;
    subcontrol-position: top left;
    left: 18px;
    top: 12px;
    padding: 0;
}

QLineEdit,
QComboBox,
QSpinBox,
QPlainTextEdit {
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 10px;
    color: palette(text);
    padding: 8px 12px;
    selection-background-color: palette(highlight);
    selection-color: palette(highlighted-text);
}

QLineEdit:focus,
QComboBox:focus,
QSpinBox:focus,
QPlainTextEdit:focus {
    border: 1px solid palette(highlight);
}

QLineEdit::placeholder {
    color: palette(mid);
}

QComboBox::drop-down,
QSpinBox::up-button,
QSpinBox::down-button {
    border: none;
    background: transparent;
    width: 24px;
}

QComboBox QAbstractItemView {
    background: palette(base);
    color: palette(text);
    border: 1px solid palette(mid);
    selection-background-color: palette(highlight);
    selection-color: palette(highlighted-text);
}

QListWidget,
QTableWidget {
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 10px;
    color: palette(text);
    padding: 0;
    selection-background-color: palette(highlight);
    selection-color: palette(highlighted-text);
}

QListWidget:focus,
QTableWidget:focus {
    border: 1px solid palette(highlight);
}

QTableWidget::item {
    padding: 6px 10px;
}

QTableWidget#mappingTable {
    border: 1px solid palette(midlight);
    alternate-background-color: palette(alternate-base);
    selection-background-color: palette(button);
    selection-color: palette(text);
}

QTableWidget#mappingTable:focus {
    border: 1px solid palette(midlight);
}

QTableWidget#mappingTable::item {
    border: none;
}

QTableWidget#mappingTable::item:selected {
    background: palette(alternate-base);
    color: palette(text);
    border: none;
}

QTableWidget#mappingTable::item:selected:active,
QTableWidget#mappingTable::item:selected:!active {
    background: palette(alternate-base);
    color: palette(text);
}

QTableWidget#mappingTable QComboBox,
QTableWidget#mappingTable QLineEdit {
    background: palette(alternate-base);
    border: 1px solid palette(mid);
    border-radius: 8px;
    padding: 4px 10px;
    selection-background-color: palette(button);
    selection-color: palette(text);
}

QTableWidget#mappingTable QComboBox {
    background: palette(alternate-base);
}

QTableWidget#mappingTable QComboBox:focus,
QTableWidget#mappingTable QLineEdit:focus {
    background: palette(alternate-base);
    border: 1px solid palette(midlight);
}

QHeaderView::section {
    background: palette(button);
    color: palette(window-text);
    border: none;
    border-bottom: 1px solid palette(mid);
    padding: 8px 10px;
    font-weight: 600;
}

QTableCornerButton::section {
    background: palette(button);
    border: none;
    border-bottom: 1px solid palette(mid);
}

QListWidget::item {
    padding: 8px 10px;
    margin: 2px 0;
    border-radius: 8px;
}

QListWidget::item:selected {
    background: palette(button);
    color: palette(window-text);
}

QPushButton {
    background: palette(button);
    border: 1px solid palette(mid);
    border-radius: 10px;
    color: palette(button-text);
    padding: 10px 16px;
    font-weight: 600;
    min-height: 16px;
}

QPushButton:hover {
    background: palette(alternate-base);
    border-color: palette(highlight);
}

QPushButton:pressed {
    background: palette(midlight);
}

QPushButton#workflowPrimaryButton {
    background: palette(highlight);
    border: 1px solid palette(highlight);
    color: palette(highlighted-text);
}

QPushButton#workflowPrimaryButton:hover {
    background: palette(link);
    border-color: palette(link);
}

QPushButton#workflowPrimaryButton:pressed {
    background: palette(highlight);
}

QCheckBox {
    color: palette(window-text);
    spacing: 8px;
}

QCheckBox::indicator {
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 4px;
    width: 16px;
    height: 16px;
}

QCheckBox::indicator:checked {
    background: palette(highlight);
    border-color: palette(highlight);
}

QCheckBox::indicator:disabled {
    background: palette(button);
}
"""


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
        self.setStyleSheet(WORKFLOW_PAGE_QSS)

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
        form_card_layout.addWidget(self.certificate_type_hint)

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
    ):
        super().__init__(
            localization,
            "page.mapping.title",
            "page.mapping.description",
        )
        self.excel_service = excel_service
        self.generator = generator
        self.columns: list[str] = []

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
        self.columns_list.setAlternatingRowColors(True)
        self.columns_list.itemDoubleClicked.connect(self._apply_selected_column_from_item)
        self.columns_list.currentRowChanged.connect(self._update_actions)
        self.use_selected_column_button = QPushButton()
        self._bind_translation(self.use_selected_column_button, "text", "button.use_selected_column")
        self.use_selected_column_button.clicked.connect(self._use_selected_column)
        self.use_selected_column_button.setEnabled(False)
        left_layout.addWidget(self.columns_label)
        left_layout.addWidget(self.columns_hint)
        left_layout.addWidget(self.columns_list)
        left_layout.addWidget(self.use_selected_column_button, alignment=Qt.AlignLeft)
        content_layout.addWidget(self.left_box, stretch=1)

        self.right_box, right_layout = self._create_card("group.placeholder_mappings")
        self.right_box.setMinimumWidth(WIDE_PANEL_MIN_WIDTH)
        self.mapping_hint = QLabel()
        self.mapping_hint.setWordWrap(True)
        self.mapping_hint.setObjectName("workflowHint")
        self._bind_translation(self.mapping_hint, "text", "hint.mapping_editor")
        self.mapping_table = QTableWidget(0, 2)
        self.mapping_table.setObjectName("mappingTable")
        self.mapping_table.setAlternatingRowColors(True)
        self.mapping_table.setShowGrid(False)
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mapping_table.verticalHeader().setVisible(False)
        self.mapping_table.verticalHeader().setDefaultSectionSize(44)
        self.mapping_table.setColumnWidth(0, 320)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mapping_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mapping_table.setMinimumHeight(300)
        self.mapping_table.itemSelectionChanged.connect(self._update_actions)

        mapping_buttons = QHBoxLayout()
        self.add_button = QPushButton()
        self.remove_button = QPushButton()
        self._bind_translation(self.add_button, "text", "button.add_mapping")
        self._bind_translation(self.remove_button, "text", "button.remove_selected")
        self.add_button.clicked.connect(self._add_mapping_row)
        self.remove_button.clicked.connect(self._remove_selected_row)
        self.remove_button.setEnabled(False)
        mapping_buttons.addWidget(self.add_button)
        mapping_buttons.addWidget(self.remove_button)
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
            self._load_columns()
            self._populate_table()
            self._refresh_validation()
        finally:
            self._loading = False

    def _load_columns(self):
        self.columns = []
        self.columns_list.clear()
        if not self.session.excel_path:
            self.columns_label.setText(self.localization.t("status.select_workbook_for_columns"))
            return

        try:
            preview = self.excel_service.inspect(self.session.excel_path)
        except Exception as exc:
            self.columns_label.setText(self.localization.t("status.could_not_inspect_workbook", error=exc))
            return

        self.columns = preview.columns
        self.columns_label.setText(
            self.localization.t(
                "status.rows_detected",
                row_count=preview.row_count,
                path=self._display_path(self.session.excel_path),
            )
        )
        for column in self.columns:
            self.columns_list.addItem(column)

    def _populate_table(self):
        self.mapping_table.setRowCount(0)
        mappings = self.session.mappings or [MappingEntry()]
        for mapping in mappings:
            self._add_mapping_row(mapping.placeholder, mapping.column_name)

    def _add_mapping_row(self, placeholder: str = "", column_name: str = ""):
        row = self.mapping_table.rowCount()
        self.mapping_table.insertRow(row)
        self.mapping_table.setRowHeight(row, 44)

        placeholder_item = QTableWidgetItem("")
        placeholder_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        self.mapping_table.setItem(row, 0, placeholder_item)
        placeholder_input = QLineEdit()
        placeholder_input.setText(placeholder)
        placeholder_input.setMinimumHeight(34)
        placeholder_input.textChanged.connect(self._sync_session_from_table)
        placeholder_input.installEventFilter(self)
        self.mapping_table.setCellWidget(row, 0, placeholder_input)

        combo = QComboBox()
        combo.addItem("")
        combo.addItems(self.columns)
        combo.setMinimumHeight(34)
        if column_name:
            combo.setCurrentText(column_name)
        combo.currentTextChanged.connect(self._sync_session_from_table)
        combo.installEventFilter(self)
        self.mapping_table.setCellWidget(row, 1, combo)
        self._update_actions()
        return row

    def _remove_selected_row(self):
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)
            self._sync_session_from_table()
        self._update_actions()

    def _use_selected_column(self):
        item = self.columns_list.currentItem()
        if item is None:
            return
        self._assign_column_to_mapping(item.text())

    def _apply_selected_column_from_item(self, item: QListWidgetItem):
        if item is None:
            return
        self._assign_column_to_mapping(item.text())

    def _assign_column_to_mapping(self, column_name: str):
        row = self.mapping_table.currentRow()
        if row < 0 or row >= self.mapping_table.rowCount():
            row = self._add_mapping_row(column_name=column_name)
            self.mapping_table.setCurrentCell(row, 0)
            return

        combo = self.mapping_table.cellWidget(row, 1)
        if isinstance(combo, QComboBox):
            combo.setCurrentText(column_name)
        self.mapping_table.setCurrentCell(row, 0)

    def _sync_session_from_table(self, *_args):
        if self._loading:
            return

        mappings: list[MappingEntry] = []
        for row in range(self.mapping_table.rowCount()):
            placeholder_widget = self.mapping_table.cellWidget(row, 0)
            placeholder = placeholder_widget.text().strip() if isinstance(placeholder_widget, QLineEdit) else ""
            combo = self.mapping_table.cellWidget(row, 1)
            column_name = combo.currentText().strip() if isinstance(combo, QComboBox) else ""

            if placeholder or column_name:
                mappings.append(MappingEntry(placeholder=placeholder, column_name=column_name))

        self.session.mappings = mappings
        self._refresh_validation()
        self._update_actions()
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
        self.mapping_table.setHorizontalHeaderLabels(
            [
                self.localization.t("table.placeholder"),
                self.localization.t("table.excel_column"),
            ]
        )
        self._refresh_validation()
        if self.session.excel_path:
            self._load_columns()
        self._update_actions()

    def _update_actions(self, *_args):
        has_selected_column = self.columns_list.currentItem() is not None
        self.use_selected_column_button.setEnabled(has_selected_column)
        has_selected_row = self.mapping_table.currentRow() >= 0 and self.mapping_table.rowCount() > 0
        self.remove_button.setEnabled(has_selected_row)

    def eventFilter(self, watched, event):
        if event.type() in (QEvent.FocusIn, QEvent.MouseButtonPress):
            self._select_row_for_editor(watched)
        return super().eventFilter(watched, event)

    def _select_row_for_editor(self, editor):
        for row in range(self.mapping_table.rowCount()):
            for column in range(self.mapping_table.columnCount()):
                if self.mapping_table.cellWidget(row, column) is editor:
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

from __future__ import annotations

from PySide6.QtCore import QEvent, QTimer, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHeaderView,
    QHBoxLayout,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QWidget,
)

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import (
    DEFAULT_OUTPUT_NAMING_SCHEMA,
    DEFAULT_PLACEHOLDER_DELIMITER,
    MappingEntry,
    derive_placeholder_boundaries,
    normalize_placeholder_delimiter,
)
from core.certificate.template_service import TemplatePlaceholderService
from core.manager.localization_manager import LocalizationManager
from gui.forms import Ui_MappingPageForm
from gui.ui.elements.combo_box import ClickSelectComboBox
from gui.workflow.base import WIDE_PANEL_MIN_WIDTH, WorkflowPage
from gui.workflow.mapping_logic import MappingContextService


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
        self.mapping_context = MappingContextService(self.excel_service, self.template_service)
        self.columns: list[str] = []
        self.detected_placeholders: list[str] = []
        self._last_detected_delimiters: tuple[str, str] | None = None
        self._delimiter_refresh_timer = QTimer(self)
        self._delimiter_refresh_timer.setSingleShot(True)
        self._delimiter_refresh_timer.setInterval(180)
        self._delimiter_refresh_timer.timeout.connect(self._auto_refresh_mapping_context)
        self.ui = Ui_MappingPageForm()
        self.form_root = QWidget()
        self.ui.setupUi(self.form_root)
        self.body_layout.addWidget(self.form_root, stretch=1)

        self.right_box = self.ui.rightBox
        self.mapping_hint = self.ui.mappingHint
        self.delimiter_label = self.ui.delimiterLabel
        self.delimiter_input = self.ui.delimiterInput
        self.template_status = self.ui.templateStatus
        self.output_naming_group = self.ui.outputNamingGroup
        self.output_naming_schema_label = self.ui.outputNamingSchemaLabel
        self.output_naming_schema_input = self.ui.outputNamingSchemaInput
        self.output_naming_schema_hint = self.ui.outputNamingSchemaHint
        self.mapping_table = self.ui.mappingTable
        self.add_button = self.ui.addButton
        self.refresh_button = self.ui.refreshButton
        self.validation_label = self.ui.validationLabel
        self.validation_summary = self.ui.validationSummary
        self.validation_output = self.ui.validationOutput

        self._bind_translation(self.ui.rightTitle, "upper_text", "group.placeholder_mappings")
        self._bind_translation(self.delimiter_label, "text", "field.placeholder_delimiter")
        self._bind_translation(self.output_naming_group, "upper_title", "group.output_naming_schema")
        self._bind_translation(self.output_naming_schema_label, "text", "field.output_naming_schema")
        self._bind_translation(self.output_naming_schema_hint, "text", "hint.output_naming_schema")
        self._bind_translation(self.add_button, "text", "button.add_mapping")
        self._bind_translation(self.refresh_button, "text", "button.refresh_mapping_data")
        self._bind_translation(self.validation_label, "text", "label.validation")

        self.mapping_hint.setWordWrap(True)
        self.right_box.setMinimumWidth(WIDE_PANEL_MIN_WIDTH)
        self.delimiter_input.setClearButtonEnabled(True)
        self.delimiter_input.textChanged.connect(self._sync_delimiter)
        self.template_status.setWordWrap(True)
        self.output_naming_schema_input.setClearButtonEnabled(True)
        self.output_naming_schema_input.setMinimumHeight(40)
        self.output_naming_schema_input.setPlaceholderText(DEFAULT_OUTPUT_NAMING_SCHEMA)
        self.output_naming_schema_input.textChanged.connect(self._sync_output_naming_schema)
        self.mapping_table.setRowCount(0)
        self.mapping_table.setColumnCount(2)
        self.mapping_table.setObjectName("mappingTable")
        self.mapping_table.setAlternatingRowColors(False)
        self.mapping_table.setShowGrid(False)
        self.mapping_table.horizontalHeader().setStretchLastSection(False)
        self.mapping_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.mapping_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.mapping_table.verticalHeader().setVisible(False)
        self.mapping_table.verticalHeader().setDefaultSectionSize(44)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mapping_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mapping_table.viewport().setObjectName("mappingTableViewport")
        self.mapping_table.itemSelectionChanged.connect(self._update_actions)
        self.add_button.clicked.connect(self._add_empty_mapping_row)
        self.refresh_button.clicked.connect(self._refresh_mapping_context)
        self.validation_summary.setWordWrap(True)
        self.validation_output.setReadOnly(True)
        self.validation_output.setMaximumBlockCount(200)

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
            self.template_status.setText(self.localization.t("status.select_template_for_placeholders"))
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
                self.template_status.setText(self.localization.t("status.no_template_placeholders_detected"))
            return
        self.template_status.setText(self.localization.t("status.refresh_to_detect_placeholders"))

    def _load_columns(self):
        self.columns = []
        if not self.session.excel_path:
            self._refresh_output_naming_tokens()
            return

        result = self.mapping_context.load_workbook_columns(self.session.excel_path)
        if result.error is not None:
            self._refresh_output_naming_tokens()
            return

        self.columns = list(result.columns)
        self._refresh_output_naming_tokens()

    def _output_naming_tokens(self) -> list[str]:
        return self.mapping_context.output_naming_tokens(self.columns)

    def _refresh_output_naming_tokens(self):
        self.output_naming_schema_input.set_token_options(self._output_naming_tokens())

    def _sync_output_naming_schema(self, *_args):
        if self._loading:
            return

        self.session.output_naming_schema = self.output_naming_schema_input.text().strip()
        self._refresh_validation()
        self.session_changed.emit()

    def _populate_table(self):
        self.mapping_table.setRowCount(0)
        mappings = self._build_mapping_rows()
        for mapping in mappings:
            self._add_mapping_row(mapping.placeholder, mapping.column_name)

    def _build_mapping_rows(self) -> list[MappingEntry]:
        merged_mappings, persisted_mappings = self.mapping_context.build_mapping_rows(
            self.detected_placeholders,
            self.session.mappings,
        )
        self.session.mappings = persisted_mappings
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

        result = self.mapping_context.detect_placeholders(self.session.template_path, delimiter)
        if result.error is not None:
            self._last_detected_delimiters = None
            self.session.detected_placeholder_delimiter = ""
            self.session.detected_placeholder_count = 0
            self.template_status.setText(
                self.localization.t("status.could_not_inspect_template", error=result.error)
            )
            return

        self.detected_placeholders = list(result.placeholders)
        self._last_detected_delimiters = derive_placeholder_boundaries(delimiter)
        self.session.detected_placeholder_delimiter = delimiter
        self.session.detected_placeholder_count = len(self.detected_placeholders)
        if self.detected_placeholders:
            self.template_status.setText(
                self.localization.t(
                    "status.detected_template_placeholders",
                    count=len(self.detected_placeholders),
                )
            )
            return

        self.template_status.setText(self.localization.t("status.no_template_placeholders_detected"))

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
        self.session.mappings = self.mapping_context.prune_stale_detected_mappings(
            self.session.mappings,
            previous_detected_placeholders,
            self.detected_placeholders,
        )

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

        combo = ClickSelectComboBox()
        combo.addItems(self.columns)
        combo.setMinimumHeight(34)
        if column_name:
            combo.setCurrentText(column_name)
        else:
            combo.setCurrentIndex(-1)
            combo.setCurrentText("")
        combo.currentTextChanged.connect(self._sync_session_from_table)
        combo.installEventFilter(self)
        self.mapping_table.setCellWidget(row, 1, self._wrap_table_editor(combo, self._create_row_delete_button()))
        self._update_actions()
        return row

    def _wrap_table_editor(self, editor: QWidget, trailing_widget: QWidget | None = None) -> QWidget:
        container = QWidget()
        container.setObjectName("mappingCellContainer")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(6)
        layout.addWidget(editor, 1)
        if trailing_widget is not None:
            layout.addWidget(trailing_widget, 0, Qt.AlignRight | Qt.AlignVCenter)
        return container

    def _create_placeholder_dropdown(self, placeholder: str) -> QComboBox:
        combo = ClickSelectComboBox()
        combo.setEditable(True)
        combo.setInsertPolicy(QComboBox.NoInsert)
        combo.setMinimumHeight(34)
        for value in self.detected_placeholders:
            if combo.findText(value) == -1:
                combo.addItem(value)
        if placeholder and combo.findText(placeholder) == -1:
            combo.addItem(placeholder)
        if placeholder:
            combo.setCurrentText(placeholder)
        else:
            combo.setCurrentIndex(-1)
            combo.clearEditText()
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

    def retranslate_page(self):
        self._refresh_mapping_help_text()
        self.mapping_table.setHorizontalHeaderLabels(
            [
                self.localization.t("table.placeholder"),
                self.localization.t("table.excel_column"),
            ]
        )
        self._load_columns()
        self._load_template_placeholders()
        self._refresh_validation()
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

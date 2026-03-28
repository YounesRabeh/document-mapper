from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
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
from core.util.system_info import open_path

PAGE_MIN_WIDTH = 860
PAGE_MIN_HEIGHT = 560
PANEL_MIN_HEIGHT = 150
EDITOR_MIN_HEIGHT = 120
WIDE_PANEL_MIN_WIDTH = 420
SIDE_PANEL_MIN_WIDTH = 260


def _ellipsis_path(path: str) -> str:
    if not path:
        return "Not selected"
    return str(Path(path))


class WorkflowPage(QWidget):
    next_requested = Signal()
    prev_requested = Signal()
    session_changed = Signal()

    def __init__(self, title: str, description: str):
        super().__init__()
        self.session = ProjectSession()
        self._loading = False
        self.setMinimumSize(PAGE_MIN_WIDTH, PAGE_MIN_HEIGHT)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 22px; font-weight: 600;")
        description_label = QLabel(description)
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: palette(mid);")

        layout.addWidget(title_label)
        layout.addWidget(description_label)

        self.body_layout = QVBoxLayout()
        self.body_layout.setSpacing(16)
        layout.addLayout(self.body_layout, stretch=1)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(12)
        layout.addLayout(self.nav_layout)

    def bind_session(self, session: ProjectSession):
        self.session = session
        self.refresh_from_session()

    def refresh_from_session(self):
        pass


class SetupPage(WorkflowPage):
    def __init__(self):
        super().__init__(
            "Setup",
            "Choose the Excel workbook, Word template, output folder, and generation options for this certificate batch.",
        )

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignLeft)
        form.setFormAlignment(Qt.AlignTop)
        form.setSpacing(12)
        self.body_layout.addLayout(form)

        self.excel_input = self._create_browse_row(
            "Workbook",
            "Select Excel workbook",
            self._browse_excel,
        )
        self.template_input = self._create_browse_row(
            "Template",
            "Select Word template",
            self._browse_template,
        )
        self.output_input = self._create_browse_row(
            "Output folder",
            "Select output folder",
            self._browse_output_dir,
        )

        form.addRow("Excel workbook", self.excel_input["container"])
        form.addRow("Word template", self.template_input["container"])
        form.addRow("Output folder", self.output_input["container"])

        self.certificate_type_input = self._create_certificate_type_dropdown()
        form.addRow("Certificate type", self.certificate_type_input)

        self.certificate_type_hint = QLabel(
            "Integrale: tipo B/C = 12 ore, tipo A = 16 ore. Retraining: tipo B/C = 4h, tipo A = 6h."
        )
        self.certificate_type_hint.setWordWrap(True)
        self.certificate_type_hint.setStyleSheet("color: palette(mid);")
        self.body_layout.addWidget(self.certificate_type_hint)

        options_box = QGroupBox("Export options")
        options_layout = QHBoxLayout(options_box)
        options_layout.setContentsMargins(12, 12, 12, 12)
        options_box.setMinimumHeight(84)

        self.export_pdf_checkbox = QCheckBox("Also export PDF")
        self.pdf_timeout_input = QSpinBox()
        self.pdf_timeout_input.setRange(10, 3600)
        self.pdf_timeout_input.setSuffix(" s")

        options_layout.addWidget(self.export_pdf_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(QLabel("PDF timeout"))
        options_layout.addWidget(self.pdf_timeout_input)
        self.body_layout.addWidget(options_box)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(72)
        self.body_layout.addWidget(self.status_label)

        next_button = QPushButton("Next: Mapping")
        next_button.clicked.connect(self._go_next)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(next_button)

        self.certificate_type_input.currentTextChanged.connect(self._sync_session)
        self.export_pdf_checkbox.toggled.connect(self._sync_session)
        self.pdf_timeout_input.valueChanged.connect(self._sync_session)

    def _create_certificate_type_dropdown(self):
        widget = QComboBox()
        widget.setMinimumWidth(520)
        widget.setMinimumHeight(36)
        for option in CERTIFICATE_TYPE_OPTIONS:
            widget.addItem(option)
        return widget

    def _create_browse_row(self, button_label: str, placeholder: str, callback):
        container = QWidget()
        container.setMinimumWidth(460)
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        text_input = QPlainTextEdit()
        text_input.setPlaceholderText(placeholder)
        text_input.setFixedHeight(36)
        text_input.setMinimumWidth(320)
        text_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_input.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        text_input.setLineWrapMode(QPlainTextEdit.NoWrap)
        browse_button = QPushButton(button_label)
        browse_button.setFixedWidth(140)
        browse_button.clicked.connect(callback)

        text_input.textChanged.connect(self._sync_session)

        layout.addWidget(text_input, stretch=1)
        layout.addWidget(browse_button)

        return {
            "container": container,
            "input": text_input,
            "button": browse_button,
        }

    def refresh_from_session(self):
        self._loading = True
        try:
            self.excel_input["input"].setPlainText(self.session.excel_path)
            self.template_input["input"].setPlainText(self.session.template_path)
            self.output_input["input"].setPlainText(self.session.output_dir)
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
            f"Workbook: {_ellipsis_path(self.session.excel_path)}",
            f"Template: {_ellipsis_path(self.session.template_path)}",
            f"Output folder: {_ellipsis_path(self.session.output_dir)}",
            f"Certificate type: {self.session.certificate_type or DEFAULT_CERTIFICATE_TYPE}",
            f"Mappings configured: {len(self.session.mappings)}",
        ]
        self.status_label.setText("\n".join(lines))

    def _sync_session(self, *_args):
        if self._loading:
            return

        self.session.excel_path = self.excel_input["input"].toPlainText().strip()
        self.session.template_path = self.template_input["input"].toPlainText().strip()
        self.session.output_dir = self.output_input["input"].toPlainText().strip()
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

    def _set_text_and_sync(self, widget: QPlainTextEdit, value: str):
        widget.setPlainText(value)
        self._sync_session()

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Excel workbook", "", "Excel Files (*.xlsx *.xls)")
        if path:
            self._set_text_and_sync(self.excel_input["input"], path)

    def _browse_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Word template", "", "Word Files (*.docx *.doc)")
        if path:
            self._set_text_and_sync(self.template_input["input"], path)

    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select output folder", self.session.output_dir or "")
        if path:
            self._set_text_and_sync(self.output_input["input"], path)

    def _go_next(self):
        self._sync_session()
        self.next_requested.emit()


class MappingPage(WorkflowPage):
    def __init__(self, excel_service: ExcelDataService, generator: CertificateGenerator):
        super().__init__(
            "Mapping",
            "Create explicit mappings between the literal placeholders used in the template and the columns available in the workbook.",
        )
        self.excel_service = excel_service
        self.generator = generator
        self.columns: list[str] = []

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)
        self.body_layout.addLayout(content_layout, stretch=1)

        left_box = QGroupBox("Workbook columns")
        left_layout = QVBoxLayout(left_box)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_box.setMinimumWidth(SIDE_PANEL_MIN_WIDTH)
        left_box.setMinimumHeight(PANEL_MIN_HEIGHT + 80)
        self.columns_label = QLabel("No workbook loaded yet.")
        self.columns_label.setWordWrap(True)
        self.columns_list = QListWidget()
        self.columns_list.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        left_layout.addWidget(self.columns_label)
        left_layout.addWidget(self.columns_list)
        content_layout.addWidget(left_box, stretch=1)

        right_box = QGroupBox("Placeholder mappings")
        right_layout = QVBoxLayout(right_box)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_box.setMinimumWidth(WIDE_PANEL_MIN_WIDTH)
        self.mapping_table = QTableWidget(0, 2)
        self.mapping_table.setHorizontalHeaderLabels(["Placeholder", "Excel column"])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        self.mapping_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.mapping_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.mapping_table.setMinimumHeight(260)
        self.mapping_table.itemChanged.connect(self._sync_session_from_table)

        mapping_buttons = QHBoxLayout()
        add_button = QPushButton("Add mapping")
        remove_button = QPushButton("Remove selected")
        add_button.clicked.connect(self._add_mapping_row)
        remove_button.clicked.connect(self._remove_selected_row)
        mapping_buttons.addWidget(add_button)
        mapping_buttons.addWidget(remove_button)
        mapping_buttons.addStretch()

        self.validation_output = QPlainTextEdit()
        self.validation_output.setReadOnly(True)
        self.validation_output.setMaximumBlockCount(200)
        self.validation_output.setMinimumHeight(EDITOR_MIN_HEIGHT)

        right_layout.addLayout(mapping_buttons)
        right_layout.addWidget(self.mapping_table, stretch=1)
        right_layout.addWidget(QLabel("Validation"))
        right_layout.addWidget(self.validation_output)
        content_layout.addWidget(right_box, stretch=2)

        back_button = QPushButton("Back")
        next_button = QPushButton("Next: Generate")
        back_button.clicked.connect(self.prev_requested.emit)
        next_button.clicked.connect(self._go_next)
        self.nav_layout.addWidget(back_button)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(next_button)

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
            self.columns_label.setText("Select a workbook on the Setup page to see available columns.")
            return

        try:
            preview = self.excel_service.inspect(self.session.excel_path)
        except Exception as exc:
            self.columns_label.setText(f"Could not inspect workbook: {exc}")
            return

        self.columns = preview.columns
        self.columns_label.setText(f"{preview.row_count} rows detected in {_ellipsis_path(self.session.excel_path)}")
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

        placeholder_item = QTableWidgetItem(placeholder)
        self.mapping_table.setItem(row, 0, placeholder_item)

        combo = QComboBox()
        combo.addItem("")
        combo.addItems(self.columns)
        if column_name:
            combo.setCurrentText(column_name)
        combo.currentTextChanged.connect(self._sync_session_from_table)
        self.mapping_table.setCellWidget(row, 1, combo)

    def _remove_selected_row(self):
        current_row = self.mapping_table.currentRow()
        if current_row >= 0:
            self.mapping_table.removeRow(current_row)
            self._sync_session_from_table()

    def _sync_session_from_table(self, *_args):
        if self._loading:
            return

        mappings: list[MappingEntry] = []
        for row in range(self.mapping_table.rowCount()):
            placeholder_item = self.mapping_table.item(row, 0)
            placeholder = placeholder_item.text().strip() if placeholder_item else ""
            combo = self.mapping_table.cellWidget(row, 1)
            column_name = combo.currentText().strip() if isinstance(combo, QComboBox) else ""

            if placeholder or column_name:
                mappings.append(MappingEntry(placeholder=placeholder, column_name=column_name))

        self.session.mappings = mappings
        self._refresh_validation()
        self.session_changed.emit()

    def _refresh_validation(self):
        errors = self.generator.validate_session(self.session)
        if errors:
            self.validation_output.setPlainText("\n".join(f"- {error}" for error in errors))
        else:
            self.validation_output.setPlainText("Ready to generate certificates.")

    def _go_next(self):
        self._sync_session_from_table()
        errors = self.generator.validate_session(self.session)
        if errors:
            QMessageBox.warning(self, "Cannot continue", "\n".join(errors))
            return
        self.next_requested.emit()


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

    def __init__(self, generator: CertificateGenerator):
        super().__init__(
            "Generate",
            "Review the current batch, validate the inputs, and run the document generation pipeline.",
        )
        self.generator = generator
        self._thread: QThread | None = None
        self._worker: GenerationWorker | None = None

        summary_box = QGroupBox("Batch summary")
        summary_layout = QVBoxLayout(summary_box)
        summary_layout.setContentsMargins(12, 12, 12, 12)
        summary_box.setMinimumHeight(PANEL_MIN_HEIGHT)
        self.summary_output = QPlainTextEdit()
        self.summary_output.setReadOnly(True)
        self.summary_output.setMinimumHeight(PANEL_MIN_HEIGHT - 24)
        summary_layout.addWidget(self.summary_output)
        self.body_layout.addWidget(summary_box)

        log_box = QGroupBox("Generation log")
        log_layout = QVBoxLayout(log_box)
        log_layout.setContentsMargins(12, 12, 12, 12)
        log_box.setMinimumHeight(PANEL_MIN_HEIGHT + 80)
        self.log_output = QPlainTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        log_layout.addWidget(self.log_output)
        self.body_layout.addWidget(log_box, stretch=1)

        back_button = QPushButton("Back")
        self.generate_button = QPushButton("Generate certificates")
        back_button.clicked.connect(self.prev_requested.emit)
        self.generate_button.clicked.connect(self._start_generation)
        self.nav_layout.addWidget(back_button)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(self.generate_button)

    def refresh_from_session(self):
        errors = self.generator.validate_session(self.session)
        summary_lines = [
            f"Workbook: {_ellipsis_path(self.session.excel_path)}",
            f"Template: {_ellipsis_path(self.session.template_path)}",
            f"Output: {_ellipsis_path(self.session.output_dir)}",
            f"Mappings: {len(self.session.mappings)}",
            f"Export PDF: {'Yes' if self.session.export_pdf else 'No'}",
            "",
            "Validation",
        ]
        if errors:
            summary_lines.extend(f"- {error}" for error in errors)
        else:
            summary_lines.append("- Ready to generate")
        self.summary_output.setPlainText("\n".join(summary_lines))

    def _start_generation(self):
        errors = self.generator.validate_session(self.session)
        if errors:
            QMessageBox.warning(self, "Cannot generate", "\n".join(errors))
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
        self.log_output.appendPlainText("Generation finished.")
        self.generate_button.setEnabled(True)
        self.results_ready.emit(result)
        self._cleanup_thread()

    def _handle_failed(self, error_message: str):
        self.log_output.appendPlainText(f"Generation failed: {error_message}")
        self.generate_button.setEnabled(True)
        QMessageBox.critical(self, "Generation failed", error_message)
        self._cleanup_thread()

    def _cleanup_thread(self):
        if self._worker is not None:
            self._worker.deleteLater()
        self._worker = None
        self._thread = None


class ResultsPage(WorkflowPage):
    def __init__(self):
        super().__init__(
            "Results",
            "Review the output from the last run, open the generated files, and inspect any generation errors.",
        )
        self.result = GenerationResult()

        self.summary_label = QLabel("No generation results yet.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setMinimumHeight(72)
        self.body_layout.addWidget(self.summary_label)

        files_box = QGroupBox("Generated files")
        files_layout = QVBoxLayout(files_box)
        files_layout.setContentsMargins(12, 12, 12, 12)
        files_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.files_list = QListWidget()
        self.files_list.setMinimumHeight(PANEL_MIN_HEIGHT)
        self.files_list.itemDoubleClicked.connect(self._open_selected_item)
        files_layout.addWidget(self.files_list)
        self.body_layout.addWidget(files_box, stretch=1)

        errors_box = QGroupBox("Errors")
        errors_layout = QVBoxLayout(errors_box)
        errors_layout.setContentsMargins(12, 12, 12, 12)
        errors_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.errors_output = QPlainTextEdit()
        self.errors_output.setReadOnly(True)
        self.errors_output.setMinimumHeight(PANEL_MIN_HEIGHT)
        errors_layout.addWidget(self.errors_output)
        self.body_layout.addWidget(errors_box, stretch=1)

        back_button = QPushButton("Back")
        open_output_button = QPushButton("Open output folder")
        open_log_button = QPushButton("Open log")
        back_button.clicked.connect(self.prev_requested.emit)
        open_output_button.clicked.connect(self._open_output_folder)
        open_log_button.clicked.connect(self._open_log)

        self.nav_layout.addWidget(back_button)
        self.nav_layout.addStretch()
        self.nav_layout.addWidget(open_log_button)
        self.nav_layout.addWidget(open_output_button)

    def bind_result(self, result: GenerationResult, session: ProjectSession):
        self.result = result
        self.session = session
        self.refresh_from_session()

    def refresh_from_session(self):
        total_files = len(self.result.generated_docx_paths) + len(self.result.generated_pdf_paths)
        summary_lines = [
            f"Created {self.result.success_count} of {self.result.total_rows} DOCX certificates.",
            f"Generated PDFs: {len(self.result.generated_pdf_paths)}",
            f"Files listed: {total_files}",
        ]
        if self.result.last_certificate_number:
            summary_lines.append(f"Last certificate number: {self.result.last_certificate_number}")
        if self.result.log_path:
            summary_lines.append(f"Log file: {self.result.log_path}")
        self.summary_label.setText("\n".join(summary_lines))

        self.files_list.clear()
        for path in [*self.result.generated_docx_paths, *self.result.generated_pdf_paths]:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.UserRole, path)
            self.files_list.addItem(item)

        if self.result.errors:
            self.errors_output.setPlainText("\n".join(self.result.errors))
        else:
            self.errors_output.setPlainText("No generation errors.")

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

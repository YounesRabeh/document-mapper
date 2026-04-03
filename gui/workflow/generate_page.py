from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtWidgets import QMessageBox, QSizePolicy, QWidget

from core.certificate.generator import CertificateGenerator
from core.certificate.models import DEFAULT_OUTPUT_NAMING_SCHEMA, GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
from gui.forms import Ui_GeneratePageForm
from gui.workflow.base import PANEL_MIN_HEIGHT, WorkflowPage


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
        except Exception as exc:  # noqa: BLE001
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

        self.ui = Ui_GeneratePageForm()
        self.form_root = QWidget()
        self.ui.setupUi(self.form_root)
        self.body_layout.addWidget(self.form_root)

        self.summary_box = self.ui.summaryBox
        self.summary_output = self.ui.summaryOutput
        self.log_box = self.ui.logBox
        self.log_output = self.ui.logOutput
        self.generate_button = self.ui.generateButton

        self._bind_translation(self.ui.summaryTitle, "upper_text", "group.batch_summary")
        self._bind_translation(self.ui.logTitle, "upper_text", "group.generation_log")
        self._bind_translation(self.generate_button, "text", "button.generate_certificates")

        self.summary_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.summary_output.setWordWrap(True)
        self.summary_output.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.summary_output.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.summary_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.summary_output.setMinimumHeight(0)

        self.log_box.setMinimumHeight(PANEL_MIN_HEIGHT + 80)
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(PANEL_MIN_HEIGHT + 40)

        self.generate_button.clicked.connect(self._start_generation)
        self.retranslate_ui()

    def refresh_from_session(self):
        errors = self.generator.validate_session(self.session)
        summary_lines = [
            self.localization.t("summary.workbook", value=self._display_path(self.session.excel_path)),
            self.localization.t(
                "summary.template",
                value=self.session.active_template_name or self.localization.t("common.not_selected"),
            ),
            self.localization.t(
                "summary.template_override",
                value=self._display_file_name(self.session.template_override_path),
            ),
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

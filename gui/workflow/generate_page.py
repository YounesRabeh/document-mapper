from __future__ import annotations

from html import escape

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

        self.summary_box = self.ui.summaryCard
        self.summary_status_panel = self.ui.summaryStatusPanel
        self.summary_status_badge = self.ui.summaryStatusBadge
        self.summary_status_title = self.ui.summaryStatusTitle
        self.summary_status_hint = self.ui.summaryStatusHint
        self.summary_output = self.ui.summaryOutput
        self.log_box = self.ui.logCard
        self.log_state_badge = self.ui.logStateBadge
        self.log_output = self.ui.logOutput
        self.action_hint = self.ui.actionHint
        self.generate_button = self.ui.generateButton

        self.form_root.setObjectName("generatePageBody")
        self.ui.summaryTitle.setObjectName("workflowCardTitle")
        self.ui.logTitle.setObjectName("workflowCardTitle")
        self._bind_translation(self.ui.summaryTitle, "upper_text", "group.batch_summary")
        self._bind_translation(self.ui.logTitle, "upper_text", "group.generation_log")
        self._bind_translation(self.generate_button, "text", "button.generate_certificates")

        self.summary_box.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.summary_output.setWordWrap(True)
        self.summary_output.setTextFormat(Qt.RichText)
        self.summary_output.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.summary_output.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.summary_output.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.summary_output.setMinimumHeight(0)
        self.summary_status_title.setWordWrap(True)
        self.summary_status_hint.setWordWrap(True)
        self.action_hint.setWordWrap(True)

        self.log_box.setMinimumHeight(PANEL_MIN_HEIGHT + 80)
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.log_output.setLineWrapMode(self.log_output.LineWrapMode.NoWrap)

        self.generate_button.clicked.connect(self._start_generation)
        self.retranslate_ui()

    def refresh_from_session(self):
        errors = self._validation_messages()
        self.summary_output.setText(self._build_summary_markup(errors))
        self._refresh_visual_state(errors)

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
        self.refresh_from_session()

    def _handle_finished(self, result: GenerationResult):
        self.log_output.appendPlainText(self.localization.t("log.generation_finished"))
        self.generate_button.setEnabled(True)
        self.results_ready.emit(result)
        self._cleanup_thread()
        self.refresh_from_session()

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
        self.refresh_from_session()

    def _cleanup_thread(self):
        if self._worker is not None:
            self._worker.deleteLater()
        self._worker = None
        self._thread = None

    def retranslate_page(self):
        self.log_output.setPlaceholderText(self.localization.t("log.placeholder"))
        self.refresh_from_session()

    def _validation_messages(self) -> list[str]:
        errors = self.generator.validate_session(self.session)
        return [self.localization.translate_runtime_text(error) for error in errors]

    def _build_summary_markup(self, errors: list[str]) -> str:
        summary_rows = [
            (
                self.localization.t("summary.label.workbook"),
                self._display_path(self.session.excel_path),
                False,
            ),
            (
                self.localization.t("summary.label.template"),
                self.session.active_template_name or self.localization.t("common.not_selected"),
                False,
            ),
            (
                self.localization.t("summary.label.template_override"),
                self._display_file_name(self.session.template_override_path),
                False,
            ),
            (
                self.localization.t("summary.label.output"),
                self._display_path(self.session.output_dir),
                False,
            ),
            (
                self.localization.t("summary.label.output_naming_schema"),
                self.session.output_naming_schema or DEFAULT_OUTPUT_NAMING_SCHEMA,
                True,
            ),
            (
                self.localization.t("summary.label.mappings"),
                str(len(self.session.mappings)),
                False,
            ),
            (
                self.localization.t("summary.label.export_pdf"),
                self.localization.t("common.yes") if self.session.export_pdf else self.localization.t("common.no"),
                False,
            ),
        ]
        rendered_rows = "".join(
            self._summary_row(label=label, value=value, monospace=monospace)
            for label, value, monospace in summary_rows
        )

        validation_items = errors or [self.localization.t("summary.ready_to_generate_short").lstrip("- ").strip()]
        rendered_validation = "".join(self._validation_row(message) for message in validation_items)
        validation_heading = escape(self.localization.t("summary.validation"))

        return (
            "<html><body>"
            "<table width='100%' cellspacing='0' cellpadding='0'>"
            f"{rendered_rows}"
            "</table>"
            "<div style='margin-top: 12px; margin-bottom: 10px; font-size: 12px; font-weight: 700;'>"
            f"{validation_heading}"
            "</div>"
            "<table width='100%' cellspacing='0' cellpadding='0'>"
            f"{rendered_validation}"
            "</table>"
            "</body></html>"
        )

    def _summary_row(self, *, label: str, value: str, monospace: bool) -> str:
        safe_label = escape(label)
        safe_value = escape(str(value or self.localization.t("common.not_selected")))
        value_style = "font-family: 'JetBrains Mono', 'Cascadia Mono', 'Consolas', monospace;" if monospace else ""
        return (
            "<tr>"
            "<td valign='top' width='170' style='padding: 0 18px 10px 0; font-size: 12px; font-weight: 700;'>"
            f"{safe_label}"
            "</td>"
            "<td valign='top' style='padding: 0 0 10px 0; font-size: 13px;"
            f"{value_style}'>"
            f"{safe_value}"
            "</td>"
            "</tr>"
        )

    def _validation_row(self, message: str) -> str:
        safe_message = escape(message)
        return (
            "<tr>"
            "<td valign='top' width='16' style='padding: 0 8px 8px 0; font-size: 13px; font-weight: 700;'>"
            "-"
            "</td>"
            "<td valign='top' style='padding: 0 0 8px 0; font-size: 13px;'>"
            f"{safe_message}"
            "</td>"
            "</tr>"
        )

    def _refresh_visual_state(self, errors: list[str]):
        if self._thread is not None:
            summary_badge = self.localization.t("generate.badge.running").upper()
            summary_title = self.localization.t("generate.status.running_title")
            summary_hint = self.localization.t("generate.status.running_detail")
            log_badge = self.localization.t("log.state.streaming").upper()
            action_hint = self.localization.t("generate.status.running_detail")
            summary_state = "running"
            log_state = "running"
        elif errors:
            summary_badge = self.localization.t("generate.badge.attention").upper()
            summary_title = self.localization.t("status.validation_issues", count=len(errors))
            summary_hint = errors[0]
            log_badge = self.localization.t("log.state.idle").upper()
            action_hint = self.localization.t("status.validation_issues", count=len(errors))
            summary_state = "attention"
            log_state = "neutral"
        else:
            summary_badge = self.localization.t("generate.badge.ready").upper()
            summary_title = self.localization.t("status.ready_to_generate")
            summary_hint = self.localization.t("status.validation_ready_detail")
            log_badge = self.localization.t("log.state.idle").upper()
            action_hint = self.localization.t("status.validation_ready_detail")
            summary_state = "ready"
            log_state = "neutral"

        self.summary_status_badge.setText(summary_badge)
        self.summary_status_title.setText(summary_title)
        self.summary_status_hint.setText(summary_hint)
        self.log_state_badge.setText(log_badge)
        self.action_hint.setText(action_hint)
        self._set_state_property(self.summary_status_badge, summary_state)
        self._set_state_property(self.log_state_badge, log_state)

    def _set_state_property(self, widget, state: str):
        if widget.property("status") == state:
            return
        widget.setProperty("status", state)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

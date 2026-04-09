from __future__ import annotations

from html import escape
from pathlib import Path
import shutil

from PySide6.QtCore import QObject, QThread, Signal, Qt
from PySide6.QtGui import QPalette, QTextCursor
from PySide6.QtWidgets import QMessageBox, QSizePolicy, QTextEdit, QWidget

from core.mapping.generator import DocumentGenerator
from core.mapping.models import DEFAULT_OUTPUT_NAMING_SCHEMA, GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
from gui.forms import Ui_GeneratePageForm
from gui.workflow.base import PANEL_MIN_HEIGHT, WorkflowPage


class GenerationWorker(QObject):
    """Background worker that runs document generation off the UI thread."""

    log_message = Signal(str)
    finished = Signal(object)
    failed = Signal(str)

    def __init__(self, generator: DocumentGenerator, session: ProjectSession):
        super().__init__()
        self.generator = generator
        self.session = session

    def run(self):
        """Execute generation and emit either finished or failed signals."""
        try:
            result = self.generator.generate(self.session, progress_callback=self.log_message.emit)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.finished.emit(result)


class GeneratePage(WorkflowPage):
    """Workflow page that validates input and executes document generation."""

    results_ready = Signal(object)

    def __init__(self, generator: DocumentGenerator, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.generate.title",
            "page.generate.description",
        )
        self.generator = generator
        self._thread: QThread | None = None
        self._worker: GenerationWorker | None = None
        self._has_generated_in_app_session = False

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
        self.log_output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self.log_output.setUndoRedoEnabled(False)
        self.log_output.document().setDocumentMargin(0)

        self.generate_button.clicked.connect(self._start_generation)
        self.retranslate_ui()

    def refresh_from_session(self):
        """Refresh summary/validation UI based on current session state."""
        errors = self._validation_messages()
        self.summary_output.setText(self._build_summary_markup(errors))
        self._refresh_visual_state(errors)

    def _start_generation(self):
        errors = self.generator.validate_session_inputs(self.session)
        if errors:
            translated = [self.localization.translate_runtime_text(error) for error in errors]
            QMessageBox.warning(self, self.localization.t("dialog.cannot_generate.title"), "\n".join(translated))
            self.refresh_from_session()
            return

        if self._thread is not None:
            return

        if self._has_generated_in_app_session and self._has_output_cache(self.session.output_dir):
            if not self._confirm_cache_reset():
                return
            try:
                self._clear_output_cache(self.session.output_dir)
            except OSError as exc:
                QMessageBox.warning(
                    self,
                    self.localization.t("dialog.cannot_generate.title"),
                    self.localization.translate_runtime_text(str(exc)),
                )
                return

        self.log_output.clear()
        self.generate_button.setEnabled(False)
        session_copy = self.session.clone()

        self._thread = QThread(self)
        self._worker = GenerationWorker(self.generator, session_copy)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.log_message.connect(self._append_log_entry)
        self._worker.finished.connect(self._handle_finished)
        self._worker.failed.connect(self._handle_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.start()
        self.refresh_from_session()

    def _confirm_cache_reset(self) -> bool:
        decision = QMessageBox.question(
            self,
            self.localization.t("dialog.generation_cache_reset.title"),
            self.localization.t("dialog.generation_cache_reset.body"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return decision == QMessageBox.StandardButton.Yes

    def _cache_artifacts(self, output_dir: str) -> list[Path]:
        if not output_dir:
            return []
        try:
            root = Path(output_dir).expanduser().resolve()
        except (OSError, ValueError):
            return []
        artifacts = [
            root / "docx",
            root / "pdf",
            root / "generation.log",
            root / "certificate_generation.log",
        ]
        return [artifact for artifact in artifacts if artifact.exists()]

    def _has_output_cache(self, output_dir: str) -> bool:
        for artifact in self._cache_artifacts(output_dir):
            if artifact.is_file():
                return True
            if artifact.is_dir() and any(artifact.iterdir()):
                return True
        return False

    def _clear_output_cache(self, output_dir: str):
        for artifact in self._cache_artifacts(output_dir):
            if artifact.is_dir():
                shutil.rmtree(artifact)
            else:
                artifact.unlink(missing_ok=True)

    def _handle_finished(self, result: GenerationResult):
        self._append_log_entry(self.localization.t("log.generation_finished"))
        if result.success_count > 0 or result.generated_docx_paths or result.generated_pdf_paths:
            self._has_generated_in_app_session = True
        self.generate_button.setEnabled(True)
        self.results_ready.emit(result)
        self._cleanup_thread()
        self.refresh_from_session()

    def _handle_failed(self, error_message: str):
        self._append_log_entry(
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
        """Refresh translated placeholders and recompute summary state."""
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

    def _append_log_entry(self, message: str):
        self.log_output.append(self._render_log_entry(message))
        self.log_output.moveCursor(QTextCursor.MoveOperation.End)
        self.log_output.ensureCursorVisible()

    def _render_log_entry(self, message: str) -> str:
        level, body = self._split_log_message(message)
        colors = self._log_level_colors(level)
        safe_level = escape(level)
        safe_body = escape(body)
        return (
            "<div style='margin: 0 0 8px 0; padding: 10px 12px; "
            f"background: {colors['row_bg']}; border: 1px solid {colors['row_border']}; border-radius: 12px;'>"
            "<table width='100%' cellspacing='0' cellpadding='0'>"
            "<tr>"
            "<td valign='top' width='92' style='padding: 0 12px 0 0;'>"
            "<span style='display: inline-block; padding: 4px 8px; border-radius: 999px; "
            f"background: {colors['badge_bg']}; color: {colors['badge_fg']}; "
            "font-size: 10px; font-weight: 800; letter-spacing: 0.8px;'>"
            f"{safe_level}"
            "</span>"
            "</td>"
            "<td valign='middle' style='font-size: 13px; line-height: 1.45; "
            f"color: {colors['text']};'>{safe_body}</td>"
            "</tr>"
            "</table>"
            "</div>"
        )

    def _split_log_message(self, message: str) -> tuple[str, str]:
        text = str(message or "").strip()
        if " | " in text:
            level, body = text.split(" | ", 1)
            return level.strip().upper(), body.strip()
        return "INFO", text

    def _log_level_colors(self, level: str) -> dict[str, str]:
        palette = self.log_output.palette()
        row_bg = palette.color(QPalette.ColorRole.AlternateBase).name()
        row_border = palette.color(QPalette.ColorRole.Midlight).name()
        default_text = palette.color(QPalette.ColorRole.WindowText).name()
        neutral_badge_fg = palette.color(QPalette.ColorRole.HighlightedText).name()
        mapping = {
            "INFO": {
                "badge_bg": "#3d6fa1",
                "badge_fg": neutral_badge_fg,
                "row_bg": row_bg,
                "row_border": row_border,
                "text": default_text,
            },
            "PROCESS": {
                "badge_bg": "#5d5ad6",
                "badge_fg": neutral_badge_fg,
                "row_bg": row_bg,
                "row_border": row_border,
                "text": default_text,
            },
            "SUCCESS": {
                "badge_bg": "#2d8a57",
                "badge_fg": neutral_badge_fg,
                "row_bg": row_bg,
                "row_border": row_border,
                "text": default_text,
            },
            "WARNING": {
                "badge_bg": "#b17a25",
                "badge_fg": neutral_badge_fg,
                "row_bg": row_bg,
                "row_border": row_border,
                "text": default_text,
            },
            "ERROR": {
                "badge_bg": "#b44747",
                "badge_fg": neutral_badge_fg,
                "row_bg": row_bg,
                "row_border": row_border,
                "text": default_text,
            },
        }
        return mapping.get(level, mapping["INFO"])

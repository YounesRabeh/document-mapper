from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QListWidgetItem, QWidget

from core.certificate.models import GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
from core.util.system_info import open_path
from gui.forms import Ui_ResultsPageForm
from gui.workflow.base import PANEL_MIN_HEIGHT, WorkflowPage


class ResultsPage(WorkflowPage):
    def __init__(self, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.results.title",
            "page.results.description",
        )
        self.result = GenerationResult()

        self.ui = Ui_ResultsPageForm()
        self.form_root = QWidget()
        self.ui.setupUi(self.form_root)
        self.body_layout.addWidget(self.form_root)

        self.summary_card = self.ui.resultsSummaryCard
        self.summary_title = self.ui.summaryTitle
        self.results_status_panel = self.ui.resultsStatusPanel
        self.results_status_badge = self.ui.resultsStatusBadge
        self.results_status_title = self.ui.resultsStatusTitle
        self.results_status_hint = self.ui.resultsStatusHint
        self.summary_label = self.ui.summaryLabel
        self.files_box = self.ui.filesCard
        self.files_title = self.ui.filesTitle
        self.files_count_badge = self.ui.filesCountBadge
        self.files_list = self.ui.filesList
        self.errors_box = self.ui.errorsCard
        self.errors_title = self.ui.errorsTitle
        self.errors_count_badge = self.ui.errorsCountBadge
        self.errors_output = self.ui.errorsOutput
        self.action_hint = self.ui.actionHint
        self.open_output_button = self.ui.openOutputButton
        self.open_log_button = self.ui.openLogButton

        self.form_root.setObjectName("resultsPageBody")
        self.summary_title.setObjectName("workflowCardTitle")
        self.files_title.setObjectName("workflowCardTitle")
        self.errors_title.setObjectName("workflowCardTitle")
        self._bind_translation(self.summary_title, "upper_text", "group.run_summary")
        self._bind_translation(self.files_title, "upper_text", "group.generated_files")
        self._bind_translation(self.errors_title, "upper_text", "group.errors")
        self._bind_translation(self.action_hint, "text", "results.action_hint")
        self._bind_translation(self.open_output_button, "text", "button.open_output_folder")
        self._bind_translation(self.open_log_button, "text", "button.open_log")

        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.RichText)
        self.summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.results_status_title.setWordWrap(True)
        self.results_status_hint.setWordWrap(True)
        self.action_hint.setWordWrap(True)

        self.files_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.files_list.setMinimumHeight(PANEL_MIN_HEIGHT)
        self.files_list.setSpacing(8)
        self.files_list.itemDoubleClicked.connect(self._open_selected_item)

        self.errors_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.errors_output.setReadOnly(True)
        self.errors_output.setMinimumHeight(PANEL_MIN_HEIGHT)
        self.open_output_button.clicked.connect(self._open_output_folder)
        self.open_log_button.clicked.connect(self._open_log)
        self.retranslate_ui()

    def bind_result(self, result: GenerationResult, session: ProjectSession):
        self.result = result
        self.session = session
        self.refresh_from_session()

    def refresh_from_session(self):
        total_files = len(self.result.generated_docx_paths) + len(self.result.generated_pdf_paths)
        error_count = len(self.result.errors)

        self.summary_label.setText(self._build_summary_markup(total_files, error_count))
        self._refresh_visual_state(total_files, error_count)

        self.files_list.clear()
        for path in [*self.result.generated_docx_paths, *self.result.generated_pdf_paths]:
            item = QListWidgetItem(Path(path).name)
            item.setData(Qt.UserRole, path)
            self.files_list.addItem(item)
        if self.files_list.count() == 0:
            placeholder_item = QListWidgetItem(self.localization.t("results.files.empty"))
            placeholder_item.setFlags(Qt.NoItemFlags)
            self.files_list.addItem(placeholder_item)

        if self.result.errors:
            translated = [self.localization.translate_runtime_text(error) for error in self.result.errors]
            self.errors_output.setPlainText("\n".join(translated))
        else:
            self.errors_output.setPlainText(self.localization.t("results.no_generation_errors"))

    def _build_summary_markup(self, total_files: int, error_count: int) -> str:
        rows: list[tuple[str, str, bool]] = []
        if total_files or self.result.total_rows:
            rows.extend(
                [
                    (
                        self.localization.t("results.metric.docx_created"),
                        self.localization.t(
                            "results.created_docx",
                            success_count=self.result.success_count,
                            total_rows=self.result.total_rows,
                        ),
                        False,
                    ),
                    (
                        self.localization.t("results.metric.pdf_generated"),
                        str(len(self.result.generated_pdf_paths)),
                        False,
                    ),
                    (
                        self.localization.t("results.metric.files_available"),
                        str(total_files),
                        False,
                    ),
                ]
            )
            if self.result.last_certificate_number:
                rows.append(
                    (
                        self.localization.t("results.metric.last_reference"),
                        self.result.last_certificate_number,
                        True,
                    )
                )
            if self.result.log_path:
                rows.append(
                    (
                        self.localization.t("results.metric.log_file"),
                        self.result.log_path,
                        True,
                    )
                )
        else:
            rows.append(
                (
                    self.localization.t("group.run_summary"),
                    self.localization.t("status.no_generation_results"),
                    False,
                )
            )
            if self.result.log_path:
                rows.append(
                    (
                        self.localization.t("results.metric.log_file"),
                        self.result.log_path,
                        True,
                    )
                )
            if error_count:
                rows.append(
                    (
                        self.localization.t("group.errors"),
                        self.localization.t("results.error_count", count=error_count),
                        False,
                    )
                )

        rendered_rows = "".join(
            self._summary_row(label=label, value=value, monospace=monospace)
            for label, value, monospace in rows
        )
        return (
            "<html><body>"
            "<table width='100%' cellspacing='0' cellpadding='0'>"
            f"{rendered_rows}"
            "</table>"
            "</body></html>"
        )

    def _summary_row(self, *, label: str, value: str, monospace: bool) -> str:
        safe_label = escape(label)
        safe_value = escape(str(value))
        value_style = "font-family: 'JetBrains Mono', 'Cascadia Mono', 'Consolas', monospace;" if monospace else ""
        return (
            "<tr>"
            "<td valign='top' width='176' style='padding: 0 18px 10px 0; font-size: 12px; font-weight: 700;'>"
            f"{safe_label}"
            "</td>"
            "<td valign='top' style='padding: 0 0 10px 0; font-size: 13px;"
            f"{value_style}'>"
            f"{safe_value}"
            "</td>"
            "</tr>"
        )

    def _refresh_visual_state(self, total_files: int, error_count: int):
        if total_files == 0 and error_count == 0 and not self.result.log_path:
            badge = self.localization.t("results.badge.empty").upper()
            title = self.localization.t("results.status.empty_title")
            hint = self.localization.t("results.status.empty_detail")
            status = "empty"
        elif error_count or (self.result.total_rows and self.result.success_count < self.result.total_rows):
            badge = self.localization.t("results.badge.warning").upper()
            title = self.localization.t("results.status.warning_title")
            hint = self.localization.t("results.status.warning_detail")
            status = "warning"
        else:
            badge = self.localization.t("results.badge.success").upper()
            title = self.localization.t("results.status.success_title")
            hint = self.localization.t("results.status.success_detail")
            status = "success"

        self.results_status_badge.setText(badge)
        self.results_status_title.setText(title)
        self.results_status_hint.setText(hint)
        self.files_count_badge.setText(str(total_files))
        self.errors_count_badge.setText(
            self.localization.t("results.errors.none_badge").upper() if error_count == 0 else str(error_count)
        )
        self._set_state_property(self.results_status_badge, status)
        self._set_state_property(self.files_count_badge, "neutral" if total_files else "empty")
        self._set_state_property(self.errors_count_badge, "success" if error_count == 0 else "warning")

    def _set_state_property(self, widget, state: str):
        if widget.property("status") == state:
            return
        widget.setProperty("status", state)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

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

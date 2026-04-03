from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QGroupBox, QLabel, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QVBoxLayout

from core.certificate.models import GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
from core.util.system_info import open_path
from gui.workflow.base import PANEL_MIN_HEIGHT, WorkflowPage


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

        self.open_output_button = QPushButton()
        self.open_log_button = QPushButton()
        self._bind_translation(self.open_output_button, "text", "button.open_output_folder")
        self._bind_translation(self.open_log_button, "text", "button.open_log")
        self.open_output_button.clicked.connect(self._open_output_folder)
        self.open_log_button.clicked.connect(self._open_log)

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
            if self.result.errors or self.result.log_path:
                summary_lines = [
                    self.localization.t("results.no_generated_documents"),
                    self.localization.t("results.generated_pdfs", count=len(self.result.generated_pdf_paths)),
                ]
                if self.result.log_path:
                    summary_lines.append(self.localization.t("results.log_file", path=self.result.log_path))
                if self.result.errors:
                    summary_lines.append(self.localization.t("results.error_count", count=len(self.result.errors)))
                self.summary_label.setText("\n".join(summary_lines))
            else:
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

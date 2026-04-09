from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from core.mapping.models import GenerationResult, ProjectSession
from core.mapping.output_archive import ArchiveCreationError, OutputArchiveService
from core.manager.localization_manager import LocalizationManager
from core.util.system_info import open_path
from gui.workflow.base import WorkflowPage


class ArchivePage(WorkflowPage):
    """Workflow page that manually archives the latest successful generation output."""

    def __init__(self, localization: LocalizationManager, archive_service: OutputArchiveService | None = None):
        super().__init__(
            localization,
            "page.archive.title",
            "page.archive.description",
        )
        self.result = GenerationResult()
        self._archive_service = archive_service or OutputArchiveService()
        self._last_archive_path: str = ""
        self._last_result_signature: tuple = ()
        self._suspend_session_sync = False

        self.card, card_layout = self._create_card("group.output_archive")
        self.body_layout.addWidget(self.card)

        self.form = QFrame()
        self.form.setObjectName("workflowCard")
        form_layout = QGridLayout(self.form)
        form_layout.setHorizontalSpacing(10)
        form_layout.setVerticalSpacing(10)
        form_layout.setContentsMargins(16, 14, 16, 14)

        self.archive_root_label = QLabel()
        self.archive_root_label.setObjectName("archiveRootLabel")
        self.archive_root_input = QLineEdit()
        self.archive_root_input.setObjectName("archiveRootInput")
        self.archive_root_input.setClearButtonEnabled(True)
        self.archive_root_browse_button = QPushButton()
        self.archive_root_browse_button.setObjectName("archiveRootBrowseButton")

        self.archive_run_name_label = QLabel()
        self.archive_run_name_label.setObjectName("archiveRunNameLabel")
        self.archive_run_name_input = QLineEdit()
        self.archive_run_name_input.setObjectName("archiveRunNameInput")
        self.archive_run_name_input.setClearButtonEnabled(True)

        self.archive_format_label = QLabel()
        self.archive_format_label.setObjectName("archiveFormatLabel")
        self.archive_format_combo = QComboBox()
        self.archive_format_combo.setObjectName("archiveFormatCombo")
        self.archive_format_combo.setMinimumWidth(140)

        self.archive_output_button = QPushButton()
        self.archive_output_button.setObjectName("archiveOutputButton")
        self.open_archive_button = QPushButton()
        self.open_archive_button.setObjectName("openArchiveButton")

        self.status_label = QLabel()
        self.status_label.setObjectName("workflowStatus")
        self.status_label.setWordWrap(True)

        form_layout.addWidget(self.archive_root_label, 0, 0)
        form_layout.addWidget(self.archive_root_input, 0, 1)
        form_layout.addWidget(self.archive_root_browse_button, 0, 2)

        form_layout.addWidget(self.archive_run_name_label, 1, 0)
        form_layout.addWidget(self.archive_run_name_input, 1, 1)

        format_actions_container = QFrame()
        format_actions_layout = QHBoxLayout(format_actions_container)
        format_actions_layout.setContentsMargins(0, 0, 0, 0)
        format_actions_layout.setSpacing(10)
        format_actions_layout.addWidget(self.archive_format_label)
        format_actions_layout.addWidget(self.archive_format_combo)
        format_actions_layout.addWidget(self.archive_output_button)
        format_actions_layout.addWidget(self.open_archive_button)
        form_layout.addWidget(format_actions_container, 1, 2)

        card_layout.addWidget(self.form)
        card_layout.addWidget(self.status_label)

        self._bind_translation(self.archive_root_label, "text", "results.archive.root_label")
        self._bind_translation(self.archive_root_input, "placeholder", "results.archive.root_placeholder")
        self._bind_translation(self.archive_root_browse_button, "text", "button.browse")
        self._bind_translation(self.archive_run_name_label, "text", "results.archive.run_name_label")
        self._bind_translation(self.archive_run_name_input, "placeholder", "results.archive.run_name_placeholder")
        self._bind_translation(self.archive_format_label, "text", "results.archive.format_label")
        self._bind_translation(self.archive_output_button, "text", "button.archive_output")
        self._bind_translation(self.open_archive_button, "text", "button.open_archive")

        self.archive_root_browse_button.clicked.connect(self._choose_archive_root)
        self.archive_output_button.clicked.connect(self._archive_output)
        self.open_archive_button.clicked.connect(self._open_archive)
        self.archive_root_input.textChanged.connect(self._sync_session_archive_root)

        self._refresh_format_combo()
        self.open_archive_button.setEnabled(False)
        self.retranslate_ui()

    def bind_result(self, result: GenerationResult, session: ProjectSession):
        """Bind latest result/session and reset one-run archive state when result changes."""
        self.result = result
        self.session = session

        signature = self._result_signature(result)
        if signature != self._last_result_signature:
            self._last_result_signature = signature
            self._last_archive_path = ""
            self.open_archive_button.setEnabled(False)
            self._set_archive_root_input(self.session.archive_root_dir or self.session.output_dir or "")
            self.archive_run_name_input.clear()

        self.refresh_from_session()

    def refresh_from_session(self):
        """Refresh control enabled state and status text from current result/session."""
        total_files = len(self.result.generated_docx_paths) + len(self.result.generated_pdf_paths)
        error_count = len(self.result.errors)
        can_archive = total_files > 0 and error_count == 0

        self.archive_root_input.setEnabled(can_archive)
        self.archive_root_browse_button.setEnabled(can_archive)
        self.archive_run_name_input.setEnabled(can_archive)
        self.archive_format_combo.setEnabled(can_archive)
        self.archive_output_button.setEnabled(can_archive)
        self.open_archive_button.setEnabled(bool(self._last_archive_path))
        self.open_archive_button.setToolTip(self._last_archive_path if self._last_archive_path else "")

        if error_count:
            self.status_label.setText(self.localization.t("results.archive.validation.errors_present"))
        elif total_files == 0:
            self.status_label.setText(self.localization.t("results.archive.validation.no_files"))
        else:
            self.status_label.setText(self.localization.t("results.archive.ready"))

    def retranslate_page(self):
        """Refresh translated labels and recompute view state."""
        self._refresh_format_combo()
        self.refresh_from_session()

    def _refresh_format_combo(self):
        current = self.archive_format_combo.currentData()
        formats = self._archive_service.available_formats()
        if not formats:
            formats = ["zip"]
        self.archive_format_combo.blockSignals(True)
        self.archive_format_combo.clear()
        for archive_format in formats:
            self.archive_format_combo.addItem(
                self.localization.t(f"results.archive.format.{archive_format}"),
                archive_format,
            )
        preferred = current if current in formats else ("folder" if "folder" in formats else formats[0])
        index = formats.index(preferred)
        self.archive_format_combo.setCurrentIndex(index)
        self.archive_format_combo.blockSignals(False)

    def _result_signature(self, result: GenerationResult) -> tuple:
        return (
            result.total_rows,
            result.success_count,
            tuple(result.generated_docx_paths),
            tuple(result.generated_pdf_paths),
            result.log_path,
            tuple(result.errors),
        )

    def _choose_archive_root(self):
        start_dir = (
            self.archive_root_input.text().strip()
            or self.session.archive_root_dir
            or self.session.output_dir
            or str(Path.home())
        )
        selected_dir = QFileDialog.getExistingDirectory(
            self,
            self.localization.t("dialog.select_archive_root.title"),
            start_dir,
        )
        if selected_dir:
            self.archive_root_input.setText(selected_dir)

    def _archive_output(self):
        archive_root = self.archive_root_input.text().strip()
        run_name = self.archive_run_name_input.text().strip()
        archive_format = str(self.archive_format_combo.currentData() or "").strip()
        self._sync_session_archive_root(archive_root)

        if not archive_root:
            QMessageBox.warning(
                self,
                self.localization.t("dialog.archive_output.title"),
                self.localization.t("results.archive.validation.root_required"),
            )
            return
        if not run_name:
            QMessageBox.warning(
                self,
                self.localization.t("dialog.archive_output.title"),
                self.localization.t("results.archive.validation.run_name_required"),
            )
            return
        if not archive_format:
            QMessageBox.warning(
                self,
                self.localization.t("dialog.archive_output.title"),
                self.localization.t("results.archive.validation.format_required"),
            )
            return

        overwrite = False
        while True:
            try:
                archive_path = self._archive_service.create_archive(
                    self.result,
                    archive_root,
                    run_name,
                    archive_format,
                    overwrite=overwrite,
                )
                break
            except ArchiveCreationError as exc:
                if exc.code == "already_exists" and not overwrite:
                    confirm = QMessageBox.question(
                        self,
                        self.localization.t("dialog.archive_overwrite.title"),
                        self.localization.t("dialog.archive_overwrite.body", path=exc.details or ""),
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No,
                    )
                    if confirm == QMessageBox.StandardButton.Yes:
                        overwrite = True
                        continue
                    return

                QMessageBox.warning(
                    self,
                    self.localization.t("dialog.archive_output.title"),
                    self._archive_error_message(exc),
                )
                return
            except Exception as exc:  # noqa: BLE001
                QMessageBox.warning(
                    self,
                    self.localization.t("dialog.archive_output.title"),
                    self.localization.t("results.archive.validation.generic_failure", error=str(exc)),
                )
                return

        self._last_archive_path = str(archive_path)
        self.open_archive_button.setEnabled(True)
        self.open_archive_button.setToolTip(self._last_archive_path)
        QMessageBox.information(
            self,
            self.localization.t("dialog.archive_output.success_title"),
            self.localization.t("results.archive.success", path=str(archive_path)),
        )
        self.refresh_from_session()

    def _archive_error_message(self, error: ArchiveCreationError) -> str:
        if error.code == "has_errors":
            return self.localization.t("results.archive.validation.errors_present")
        if error.code == "no_files":
            return self.localization.t("results.archive.validation.no_files")
        if error.code == "invalid_root":
            return self.localization.t("results.archive.validation.invalid_root")
        if error.code == "invalid_run_name":
            return self.localization.t("results.archive.validation.invalid_run_name")
        if error.code == "unsupported_format":
            return self.localization.t("results.archive.validation.unsupported_format")
        if error.code == "missing_source_file":
            return self.localization.t("results.archive.validation.missing_source_file", path=error.details or "")
        if error.code == "write_failed":
            return self.localization.t("results.archive.validation.write_failed", error=error.details or "")
        return self.localization.t("results.archive.validation.generic_failure", error=str(error))

    def _open_archive(self):
        if self._last_archive_path:
            open_path(self._last_archive_path)

    def _sync_session_archive_root(self, _value: str):
        if self._suspend_session_sync:
            return
        normalized_value = self.archive_root_input.text().strip()
        if self.session.archive_root_dir == normalized_value:
            return
        self.session.archive_root_dir = normalized_value
        self.session_changed.emit()

    def _set_archive_root_input(self, value: str):
        self._suspend_session_sync = True
        try:
            self.archive_root_input.setText(value)
        finally:
            self._suspend_session_sync = False

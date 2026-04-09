from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

from core.manager.localization_manager import LocalizationManager
from gui.forms import Ui_SetupPageForm
from gui.workflow.base import WorkflowPage


class SetupPage(WorkflowPage):
    """Workflow page for setup inputs (workbook, output, runtime options)."""

    def __init__(self, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.setup.title",
            "page.setup.description",
        )
        self.ui = Ui_SetupPageForm()
        self.form_root = QWidget()
        self.ui.setupUi(self.form_root)
        self.form_root.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.ui.rootLayout.setSizeConstraint(self.ui.rootLayout.SizeConstraint.SetMinimumSize)
        self.body_layout.addWidget(self.form_root)

        self.form_card = self.ui.formCard
        self.template_override_card = self.ui.templateOverrideCard
        self.template_override_hint = self.ui.templateOverrideHint
        self.clear_override_button = self.ui.clearOverrideButton
        self.options_card = self.ui.optionsCard
        self.export_pdf_checkbox = self.ui.exportPdfCheckBox
        self.pdf_timeout_input = self.ui.pdfTimeoutSpinBox

        self.excel_input = {
            "container": self.ui.excelInputContainer,
            "input": self.ui.excelLineEdit,
            "button": self.ui.excelBrowseButton,
        }
        self.output_input = {
            "container": self.ui.outputInputContainer,
            "input": self.ui.outputLineEdit,
            "button": self.ui.outputBrowseButton,
        }
        self.template_override_input = {
            "container": self.ui.templateOverrideInputContainer,
            "input": self.ui.templateOverrideLineEdit,
            "button": self.ui.templateOverrideBrowseButton,
        }

        self._bind_translation(self.ui.formCardTitle, "upper_text", "card.project_inputs")
        self._bind_translation(self.ui.excelLabel, "text", "field.excel_workbook")
        self._bind_translation(self.excel_input["input"], "placeholder", "placeholder.select_excel_workbook")
        self._bind_translation(self.excel_input["button"], "text", "button.workbook")
        self._bind_translation(self.ui.outputLabel, "text", "field.output_folder")
        self._bind_translation(self.output_input["input"], "placeholder", "placeholder.select_output_folder")
        self._bind_translation(self.output_input["button"], "text", "button.output_folder")
        self._bind_translation(self.ui.templateOverrideTitle, "upper_text", "card.template_override")
        self._bind_translation(self.ui.templateOverrideLabel, "text", "field.template_override")
        self._bind_translation(
            self.template_override_input["input"],
            "placeholder",
            "placeholder.select_word_template",
        )
        self._bind_translation(self.template_override_input["button"], "text", "button.template")
        self._bind_translation(self.clear_override_button, "text", "button.clear_override")
        self._bind_translation(self.template_override_hint, "text", "hint.template_override")
        self._bind_translation(self.ui.optionsTitle, "upper_text", "card.export_options")
        self._bind_translation(self.export_pdf_checkbox, "text", "checkbox.export_pdf")
        self._bind_translation(self.ui.pdfTimeoutLabel, "text", "field.pdf_timeout")

        self.pdf_timeout_input.setRange(10, 3600)
        self.pdf_timeout_input.setSuffix(" s")
        self.excel_input["button"].clicked.connect(self._browse_excel)
        self.output_input["button"].clicked.connect(self._browse_output_dir)
        self.template_override_input["button"].clicked.connect(self._browse_template_override)
        self.clear_override_button.clicked.connect(self._clear_template_override)

        self.export_pdf_checkbox.toggled.connect(self._sync_session)
        self.pdf_timeout_input.valueChanged.connect(self._sync_session)
        self.retranslate_ui()
        for row in (self.excel_input, self.output_input, self.template_override_input):
            row["input"].textChanged.connect(self._sync_session)

    def refresh_from_session(self):
        """Load session values into setup controls."""
        self._loading = True
        try:
            self.excel_input["input"].setText(self.session.excel_path)
            self.output_input["input"].setText(self.session.output_dir)
            self.template_override_input["input"].setText(self.session.template_override_path)
            self.export_pdf_checkbox.setChecked(self.session.export_pdf)
            self.pdf_timeout_input.setValue(self.session.pdf_timeout_seconds)
        finally:
            self._loading = False

    def _sync_session(self, *_args):
        if self._loading:
            return

        self.session.excel_path = self.excel_input["input"].text().strip()
        self.session.output_dir = self.output_input["input"].text().strip()
        self.session.template_override_path = self.template_override_input["input"].text().strip()
        self.session.export_pdf = self.export_pdf_checkbox.isChecked()
        self.session.pdf_timeout_seconds = self.pdf_timeout_input.value()
        self.session_changed.emit()

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

    def _browse_template_override(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.localization.t("dialog.select_word_template.title"),
            "",
            self.localization.t("dialog.word_files"),
        )
        if path:
            self._set_text_and_sync(self.template_override_input["input"], path)

    def _clear_template_override(self):
        self._set_text_and_sync(self.template_override_input["input"], "")

    def _browse_output_dir(self):
        path = QFileDialog.getExistingDirectory(
            self,
            self.localization.t("dialog.select_output_folder.title"),
            self.session.output_dir or "",
        )
        if path:
            self._set_text_and_sync(self.output_input["input"], path)

    def retranslate_page(self):
        """Setup page translations are driven by bindings; no extra work required."""
        pass

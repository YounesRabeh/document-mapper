from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget,
)

from core.manager.localization_manager import LocalizationManager
from gui.workflow.base import WorkflowPage


class SetupPage(WorkflowPage):
    def __init__(self, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.setup.title",
            "page.setup.description",
        )

        form_card, form_card_layout = self._create_card("card.project_inputs")
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
        self.output_input = self._create_browse_row(
            "button.output_folder",
            "placeholder.select_output_folder",
            self._browse_output_dir,
        )

        self._add_browse_row(form, 0, "field.excel_workbook", self.excel_input)
        self._add_browse_row(form, 1, "field.output_folder", self.output_input)

        self.template_override_card, override_layout = self._create_card("card.template_override")
        override_form = QGridLayout()
        override_form.setContentsMargins(0, 0, 0, 0)
        override_form.setHorizontalSpacing(16)
        override_form.setVerticalSpacing(10)
        override_form.setColumnMinimumWidth(0, 128)
        override_form.setColumnStretch(1, 1)
        override_form.setColumnMinimumWidth(2, 148)
        override_layout.addLayout(override_form)
        self.body_layout.addWidget(self.template_override_card)

        self.template_override_input = self._create_browse_row(
            "button.template",
            "placeholder.select_word_template",
            self._browse_template_override,
        )
        override_form.addWidget(self._create_field_label("field.template_override"), 0, 0)
        override_form.addWidget(self.template_override_input["container"], 0, 1)
        override_actions = QWidget()
        override_actions_layout = QHBoxLayout(override_actions)
        override_actions_layout.setContentsMargins(0, 0, 0, 0)
        override_actions_layout.setSpacing(8)
        override_actions_layout.addWidget(self.template_override_input["button"])
        self.clear_override_button = QPushButton()
        self._bind_translation(self.clear_override_button, "text", "button.clear_override")
        self.clear_override_button.setMinimumWidth(110)
        self.clear_override_button.setMinimumHeight(40)
        self.clear_override_button.clicked.connect(self._clear_template_override)
        override_actions_layout.addWidget(self.clear_override_button)
        override_form.addWidget(override_actions, 0, 2)

        self.template_override_hint = QLabel()
        self.template_override_hint.setWordWrap(True)
        self.template_override_hint.setObjectName("workflowHint")
        self._bind_translation(self.template_override_hint, "text", "hint.template_override")
        override_form.addWidget(self.template_override_hint, 1, 1, 1, 2)

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
        self.status_label.setMinimumHeight(96)
        status_card_layout.addWidget(self.status_label)
        self.body_layout.addWidget(status_card)

        self.export_pdf_checkbox.toggled.connect(self._sync_session)
        self.pdf_timeout_input.valueChanged.connect(self._sync_session)
        self.retranslate_ui()

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
            self.output_input["input"].setText(self.session.output_dir)
            self.template_override_input["input"].setText(self.session.template_override_path)
            self.export_pdf_checkbox.setChecked(self.session.export_pdf)
            self.pdf_timeout_input.setValue(self.session.pdf_timeout_seconds)
        finally:
            self._loading = False
        self._refresh_status()

    def _refresh_status(self):
        lines = [
            self.localization.t("summary.workbook", value=self._display_file_name(self.session.excel_path)),
            self.localization.t(
                "summary.template",
                value=self.session.active_template_name or self.localization.t("common.not_selected"),
            ),
            self.localization.t(
                "summary.template_override",
                value=self._display_file_name(self.session.template_override_path),
            ),
            self.localization.t("summary.output_folder", value=self._display_folder_name(self.session.output_dir)),
            self.localization.t("summary.mappings_configured", count=len(self.session.mappings)),
        ]
        self.status_label.setText("\n".join(lines))

    def _sync_session(self, *_args):
        if self._loading:
            return

        self.session.excel_path = self.excel_input["input"].text().strip()
        self.session.output_dir = self.output_input["input"].text().strip()
        self.session.template_override_path = self.template_override_input["input"].text().strip()
        self.session.export_pdf = self.export_pdf_checkbox.isChecked()
        self.session.pdf_timeout_seconds = self.pdf_timeout_input.value()
        self._refresh_status()
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
        self._refresh_status()

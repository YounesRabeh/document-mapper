from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QInputDialog,
    QLineEdit,
    QLabel,
    QListWidgetItem,
    QMessageBox,
    QDialog,
)

from core.mapping.models import (
    DEFAULT_IMPORTED_TEMPLATE_TYPE,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
    normalize_template_name,
    normalize_template_type_name,
)
from core.manager.localization_manager import LocalizationManager
from gui.forms import Ui_TemplateManagerDialog
from gui.styles import apply_stylesheet


class TemplateManagerDialog(QDialog):
    def __init__(self, session: ProjectSession, localization: LocalizationManager, parent=None):
        super().__init__(parent)
        self.localization = localization
        self.session = session.clone()

        self.setModal(True)
        self.ui = Ui_TemplateManagerDialog()
        self.ui.setupUi(self)

        self.type_title = self.ui.typeTitle
        self.type_list = self.ui.typeList
        self.type_add_button = self.ui.typeAddButton
        self.type_rename_button = self.ui.typeRenameButton
        self.type_remove_button = self.ui.typeRemoveButton
        self.template_title = self.ui.templateTitle
        self.template_list = self.ui.templateList
        self.template_add_button = self.ui.templateAddButton
        self.template_rename_button = self.ui.templateRenameButton
        self.template_remove_button = self.ui.templateRemoveButton
        self.status_label = self.ui.statusLabel
        self.cancel_button = self.ui.cancelButton
        self.save_button = self.ui.saveButton

        self.type_title.setProperty("sectionTitle", True)
        self.template_title.setProperty("sectionTitle", True)
        apply_stylesheet(self, "template_manager_dialog")

        self.type_list.currentItemChanged.connect(self._refresh_template_list)
        self.template_list.currentItemChanged.connect(self._refresh_actions)
        self.type_add_button.clicked.connect(self._add_type)
        self.type_rename_button.clicked.connect(self._rename_type)
        self.type_remove_button.clicked.connect(self._remove_type)
        self.template_add_button.clicked.connect(self._import_templates)
        self.template_rename_button.clicked.connect(self._rename_template)
        self.template_remove_button.clicked.connect(self._remove_template)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self.accept)

        self._retranslate()
        self._refresh_type_list()

    def _retranslate(self):
        self.setWindowTitle(self.localization.t("dialog.manage_templates.title"))
        self.type_title.setText(self.localization.t("dialog.manage_templates.types"))
        self.template_title.setText(self.localization.t("dialog.manage_templates.templates"))
        self.type_add_button.setText(self.localization.t("button.add_template_type"))
        self.type_rename_button.setText(self.localization.t("button.rename_template_type"))
        self.type_remove_button.setText(self.localization.t("button.remove_template_type"))
        self.template_add_button.setText(self.localization.t("button.import_template"))
        self.template_rename_button.setText(self.localization.t("button.rename_template"))
        self.template_remove_button.setText(self.localization.t("button.remove_template"))
        self.cancel_button.setText(self.localization.t("button.cancel"))
        self.save_button.setText(self.localization.t("button.save"))

    def edited_session(self) -> ProjectSession:
        return self.session.clone()

    def _refresh_type_list(self):
        self.type_list.clear()
        for template_type in self.session.template_types:
            item = QListWidgetItem(template_type.name)
            item.setData(Qt.UserRole, template_type.name)
            self.type_list.addItem(item)

        selected_name = self.session.selected_template_type
        for row in range(self.type_list.count()):
            item = self.type_list.item(row)
            if item.data(Qt.UserRole) == selected_name:
                self.type_list.setCurrentRow(row)
                break
        else:
            if self.type_list.count() > 0:
                self.type_list.setCurrentRow(0)
        self._refresh_template_list()

    def _refresh_template_list(self):
        current_type = self._current_type_name()
        self.template_list.clear()
        for template in self.session.templates_for_type(current_type):
            item = QListWidgetItem(template.label)
            item.setData(Qt.UserRole, template.id)
            self.template_list.addItem(item)

        selected_template = self.session.selected_template
        for row in range(self.template_list.count()):
            item = self.template_list.item(row)
            if item.data(Qt.UserRole) == selected_template:
                self.template_list.setCurrentRow(row)
                break
        else:
            if self.template_list.count() > 0:
                self.template_list.setCurrentRow(0)
        self._refresh_actions()

    def _refresh_actions(self):
        has_type = bool(self._current_type_name())
        has_template = self._current_template_entry() is not None
        self.type_rename_button.setEnabled(has_type)
        self.type_remove_button.setEnabled(has_type)
        self.template_add_button.setEnabled(has_type)
        self.template_rename_button.setEnabled(has_template)
        self.template_remove_button.setEnabled(has_template)

        template_entry = self._current_template_entry()
        if template_entry is None:
            self.status_label.setText(self.localization.t("status.no_project_templates"))
            return
        if template_entry.is_managed:
            self.status_label.setText(
                self.localization.t(
                    "status.template_stored_in_project",
                    path=template_entry.relative_path or template_entry.label,
                )
            )
            return
        self.status_label.setText(
            self.localization.t(
                "status.template_pending_import",
                path=template_entry.source_path or template_entry.label,
            )
        )

    def _current_type_name(self) -> str:
        item = self.type_list.currentItem()
        return str(item.data(Qt.UserRole)).strip() if item is not None else ""

    def _current_template_entry(self) -> ProjectTemplateEntry | None:
        item = self.template_list.currentItem()
        template_id = str(item.data(Qt.UserRole)).strip() if item is not None else ""
        if not template_id:
            return None
        return next((entry for entry in self.session.templates if entry.id == template_id), None)

    def _add_type(self):
        value, accepted = self._prompt_text(
            self.localization.t("dialog.add_template_type.title"),
            self.localization.t("dialog.add_template_type.prompt"),
        )
        if not accepted:
            return
        normalized = normalize_template_type_name(value)
        if not normalized:
            return
        if any(entry.name.casefold() == normalized.casefold() for entry in self.session.template_types):
            QMessageBox.warning(
                self,
                self.localization.t("dialog.manage_templates.title"),
                self.localization.t("dialog.template_type_exists", name=normalized),
            )
            return
        self.session.template_types.append(ProjectTemplateType(normalized))
        self.session.selected_template_type = normalized
        self._refresh_type_list()

    def _rename_type(self):
        current_name = self._current_type_name()
        if not current_name:
            return
        value, accepted = self._prompt_text(
            self.localization.t("dialog.rename_template_type.title"),
            self.localization.t("dialog.rename_template_type.prompt"),
            text=current_name,
        )
        if not accepted:
            return
        normalized = normalize_template_type_name(value)
        if not normalized:
            return
        if normalized.casefold() != current_name.casefold() and any(
            entry.name.casefold() == normalized.casefold() for entry in self.session.template_types
        ):
            QMessageBox.warning(
                self,
                self.localization.t("dialog.manage_templates.title"),
                self.localization.t("dialog.template_type_exists", name=normalized),
            )
            return

        for entry in self.session.template_types:
            if entry.name == current_name:
                entry.name = normalized
        for template in self.session.templates:
            if template.type_name == current_name:
                template.type_name = normalized
        if self.session.selected_template_type == current_name:
            self.session.selected_template_type = normalized
        self._refresh_type_list()

    def _remove_type(self):
        current_name = self._current_type_name()
        if not current_name:
            return
        template_count = len(self.session.templates_for_type(current_name))
        answer = QMessageBox.question(
            self,
            self.localization.t("dialog.remove_template_type.title"),
            self.localization.t(
                "dialog.remove_template_type.body",
                name=current_name,
                count=template_count,
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.session.template_types = [entry for entry in self.session.template_types if entry.name != current_name]
        removed_template_ids = {entry.id for entry in self.session.templates if entry.type_name == current_name}
        self.session.templates = [entry for entry in self.session.templates if entry.type_name != current_name]
        if self.session.selected_template_type == current_name:
            self.session.selected_template_type = ""
        if self.session.selected_template in removed_template_ids:
            self.session.selected_template = ""
        self.session._ensure_template_catalog_consistency()
        self._refresh_type_list()

    def _import_templates(self):
        current_type = self._current_type_name()
        if not current_type:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            self.localization.t("dialog.select_project_templates.title"),
            "",
            self.localization.t("dialog.word_files"),
        )
        if not paths:
            return

        for raw_path in paths:
            source_path = Path(raw_path).expanduser().resolve()
            display_name = self._unique_template_display_name(current_type, normalize_template_name(source_path.stem))
            self.session.templates.append(
                ProjectTemplateEntry(
                    display_name=display_name,
                    type_name=current_type,
                    source_path=str(source_path),
                    is_managed=False,
                )
            )

        if self.session.selected_template_type != current_type:
            self.session.selected_template_type = current_type
        entries = self.session.templates_for_type(current_type)
        if entries:
            self.session.selected_template = entries[-1].id
        self._refresh_template_list()

    def _rename_template(self):
        template_entry = self._current_template_entry()
        if template_entry is None:
            return
        value, accepted = self._prompt_text(
            self.localization.t("dialog.rename_template.title"),
            self.localization.t("dialog.rename_template.prompt"),
            text=template_entry.label,
        )
        if not accepted:
            return
        normalized = normalize_template_name(value)
        if not normalized:
            return
        template_entry.display_name = self._unique_template_display_name(
            template_entry.type_name,
            normalized,
            exclude_template_id=template_entry.id,
        )
        self._refresh_template_list()

    def _remove_template(self):
        template_entry = self._current_template_entry()
        if template_entry is None:
            return
        self.session.templates = [entry for entry in self.session.templates if entry.id != template_entry.id]
        if self.session.selected_template == template_entry.id:
            self.session.selected_template = ""
        self.session._ensure_template_catalog_consistency()
        self._refresh_template_list()

    def _unique_template_display_name(
        self,
        type_name: str,
        base_name: str,
        exclude_template_id: str = "",
    ) -> str:
        normalized = normalize_template_name(base_name) or "Template"
        existing = {
            entry.label.casefold()
            for entry in self.session.templates_for_type(type_name)
            if entry.id != exclude_template_id
        }
        candidate = normalized
        counter = 2
        while candidate.casefold() in existing:
            candidate = f"{normalized} {counter}"
            counter += 1
        return candidate

    def _prompt_text(self, title: str, label: str, text: str = "") -> tuple[str, bool]:
        dialog = QInputDialog(self)
        dialog.setWindowTitle(title)
        dialog.setLabelText(label)
        dialog.setTextValue(text)
        dialog.setInputMode(QInputDialog.InputMode.TextInput)
        dialog.resize(520, dialog.sizeHint().height())
        dialog.setMinimumWidth(520)

        line_edit = dialog.findChild(QLineEdit)
        if line_edit is not None:
            line_edit.setMinimumWidth(360)
            line_edit.selectAll()

        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        return dialog.textValue(), accepted

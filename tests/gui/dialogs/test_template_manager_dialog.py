from __future__ import annotations

from unittest.mock import patch

from PySide6.QtWidgets import QMessageBox

from core.mapping.models import ProjectSession, ProjectTemplateEntry, ProjectTemplateType
from core.manager.localization_manager import LocalizationManager
from gui.dialogs.template_manager_dialog import TemplateManagerDialog


def test_remove_template_type_requires_confirmation(qapp, window_config, clear_test_settings):
    localization = LocalizationManager(window_config)
    template_type = ProjectTemplateType("Letters")
    template_entry = ProjectTemplateEntry(
        display_name="Letter 01",
        type_name=template_type.name,
        source_path="/tmp/letter.docx",
        is_managed=False,
    )
    session = ProjectSession(
        template_types=[template_type],
        templates=[template_entry],
        selected_template_type=template_type.name,
        selected_template=template_entry.id,
    )
    dialog = TemplateManagerDialog(session, localization)
    dialog.type_list.setCurrentRow(0)

    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Cancel):
        dialog._remove_type()

    assert [entry.name for entry in dialog.session.template_types] == ["Letters"]
    assert [entry.label for entry in dialog.session.templates] == ["Letter 01"]

    with patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes):
        dialog._remove_type()

    assert dialog.session.template_types == []
    assert dialog.session.templates == []

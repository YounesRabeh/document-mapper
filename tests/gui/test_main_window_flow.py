from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QDialog

from core.certificate.models import (
    GenerationResult,
    MappingEntry,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
)
from tests.helpers.gui import assert_stage_state, mapping_combo


def _unlock_generate_stage(window):
    window.stage_cards[2].clicked.emit(2)
    column_combo = mapping_combo(window, 0, 1)
    column_combo.setCurrentText("NAME")
    window.mapping_page._sync_session_from_table()
    window.mapping_page.refresh_button.click()


def test_workflow_rail_stays_synced_with_real_stage_state(prepared_window):
    window = prepared_window.window

    assert len(window.stage_cards) == 4
    assert window.sidebar_title.text() == "Workflow"
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)
    assert_stage_state(window, 2, active=False, blocked=False, completed=False)
    assert_stage_state(window, 3, active=False, blocked=True, completed=False)
    assert_stage_state(window, 4, active=False, blocked=True, completed=False)

    window.stage_manager.setCurrentIndex(2)
    assert window.stage_manager.currentIndex() == 0
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)

    assert not hasattr(window.setup_page, "certificate_type_input")
    assert window.template_type_combo.count() == 1
    assert window.template_type_combo.currentText() == "General"
    assert window.template_combo.count() == 1
    assert window.template_combo.currentText() == "template"
    assert "Active template: template" in window.template_toolbar_status.text()

    window.stage_cards[2].clicked.emit(2)
    assert window.stage_manager.currentIndex() == 1
    assert_stage_state(window, 1, completed=True)
    assert_stage_state(window, 2, active=True, blocked=False, completed=False)
    assert_stage_state(window, 4, blocked=True)

    window.stage_cards[4].clicked.emit(4)
    assert window.stage_manager.currentIndex() == 1


def test_generation_results_and_localization_keep_workflow_state(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)

    assert len(window.session.mappings) == 1
    assert window.session.mappings[0].column_name == "NAME"
    assert_stage_state(window, 3, blocked=False, completed=False)
    assert window.session.detected_placeholder_delimiter == "<"
    assert window.session.detected_placeholder_count == 1
    assert window.session.active_template_name == "template"

    window.stage_cards[3].clicked.emit(3)
    assert window.stage_manager.currentIndex() == 2
    assert_stage_state(window, 2, completed=True)
    assert_stage_state(window, 3, active=True, blocked=False)

    result = GenerationResult(
        total_rows=1,
        success_count=1,
        generated_docx_paths=[str(Path(temp_dir) / "docx" / "ADA_attestato_certificato.docx")],
        generated_pdf_paths=[],
        log_path=str(Path(temp_dir) / "certificate_generation.log"),
        errors=[],
    )
    window._handle_generation_result(result)

    assert window.stage_manager.currentIndex() == 3
    assert "Created 1 of 1 DOCX documents." in window.results_page.summary_label.text()
    assert_stage_state(window, 3, completed=True)
    assert_stage_state(window, 4, active=True, blocked=False)

    window.localization.set_language("it")

    assert window.view_menu.title() == "Visualizza"
    assert hasattr(window.setup_page, "next_button") is False
    assert "esempio" in window.mapping_page.mapping_hint.text()
    assert window.mapping_page.output_naming_schema_label.text() == "Schema nome output"
    assert window.template_type_label.text() == "Tipo template"
    assert "Creati 1 documenti DOCX su 1." in window.results_page.summary_label.text()
    assert_stage_state(window, 4, active=True, blocked=False)


def test_manage_templates_accepts_dialog_and_updates_session(prepared_window):
    window = prepared_window.window
    main_window_module = prepared_window.main_window_module

    edited_session = window.session.clone()
    edited_session.template_types.append(ProjectTemplateType("Letters"))

    class FakeTemplateDialog:
        def __init__(self, session, localization, parent):
            self._session = edited_session

        def exec(self):
            return QDialog.DialogCode.Accepted

        def edited_session(self):
            return self._session.clone()

    with patch.object(main_window_module, "TemplateManagerDialog", FakeTemplateDialog):
        window._manage_templates()

    assert any(entry.name == "Letters" for entry in window.session.template_types)


def test_specific_template_section_is_always_visible(prepared_window):
    window = prepared_window.window

    assert window.setup_page.template_override_card.isHidden() is False
    assert window.setup_page.template_override_input["container"].isHidden() is False
    assert window.setup_page.template_override_hint.isHidden() is False

    window.session.template_override_path = str(prepared_window.files.template)
    window.setup_page.refresh_from_session()
    assert "One-time template: template.docx" in window.setup_page.status_label.text()

    window.localization.set_language("it")
    assert window.setup_page.clear_override_button.text() == "Rimuovi template monouso"


def test_new_project_and_open_project_recompute_workflow_states(prepared_window):
    window = prepared_window.window
    fake_store = prepared_window.fake_store
    main_window_module = prepared_window.main_window_module
    workbook = prepared_window.files.workbook
    template = prepared_window.files.template
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)
    assert_stage_state(window, 3, blocked=False)

    window._new_project()
    assert window.stage_manager.currentIndex() == 0
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)
    assert_stage_state(window, 3, active=False, blocked=True, completed=False)
    assert_stage_state(window, 4, active=False, blocked=True, completed=False)
    assert window.template_type_combo.isEnabled() is True
    assert window.template_type_combo.currentText() == "Default template"
    assert window.template_combo.currentText() == "Default template 01"

    fake_store.loaded_session = ProjectSession(
        excel_path=str(workbook),
        output_dir=str(temp_dir),
        template_types=[ProjectTemplateType("Default template")],
        templates=[
            ProjectTemplateEntry(
                display_name="Default template 01",
                type_name="Default template",
                source_path=str(template),
                is_managed=False,
            )
        ],
        selected_template_type="Default template",
        placeholder_delimiter="<",
        detected_placeholder_delimiter="<",
        detected_placeholder_count=1,
        mappings=[MappingEntry(placeholder="<NAME>", column_name="NAME")],
    )
    fake_store.loaded_session.selected_template = fake_store.loaded_session.templates[0].id
    with patch.object(main_window_module.QFileDialog, "getExistingDirectory", return_value=""), patch.object(
        main_window_module.QFileDialog,
        "getOpenFileName",
        return_value=("project.json", ""),
    ):
        window._open_project()

    assert window.stage_manager.currentIndex() == 0
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)
    assert_stage_state(window, 3, active=False, blocked=False, completed=False)
    assert_stage_state(window, 4, active=False, blocked=True, completed=False)
    assert window.template_type_combo.currentText() == "Default template"
    assert window.template_combo.currentText() == "Default template 01"

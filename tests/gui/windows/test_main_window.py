from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QDialog

from core.certificate.models import (
    GenerationResult,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
)
from core.enums.app_themes import AppTheme
from core.manager.theme_manager import ThemeManager
from tests.helpers.gui import assert_stage_state, mapping_combo
from tests.helpers.fakes import FakeSessionStore


def _unlock_generate_stage(window):
    window.stage_cards[2].clicked.emit(2)
    placeholder_combo = mapping_combo(window, 0, 0)
    placeholder_combo.setCurrentText("<NAME>")
    column_combo = mapping_combo(window, 0, 1)
    column_combo.setCurrentText("NAME")
    window.mapping_page._sync_session_from_table()
    window.mapping_page.refresh_button.click()


def test_workflow_rail_stays_synced_with_real_stage_state(prepared_window):
    window = prepared_window.window

    assert len(window.stage_cards) == 4
    assert window.sidebar_title.text() == "Workflow"
    assert window.template_toolbar.isHidden() is False
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
    assert window.template_toolbar.isHidden() is True
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
    assert window.setup_page.template_override_input["input"].text() == str(prepared_window.files.template)

    window.localization.set_language("it")
    assert window.setup_page.clear_override_button.text() == "Rimuovi template monouso"


def test_last_session_keeps_managed_template_available_without_resaving(main_window_factory, tmp_path):
    project_dir = tmp_path / "saved-project"
    templates_dir = project_dir / "templates"
    templates_dir.mkdir(parents=True)
    template_path = templates_dir / "docx_template_test.docx"
    template_path.write_text("template", encoding="utf-8")

    template_type = ProjectTemplateType("test")
    template_entry = ProjectTemplateEntry(
        display_name="docx_template_test",
        type_name=template_type.name,
        relative_path="templates/docx_template_test.docx",
        is_managed=True,
    )
    last_session = ProjectSession(
        excel_path="/tmp/data.xlsx",
        output_dir="/tmp/out",
        template_path=str(template_path),
        selected_template_type=template_type.name,
        selected_template=template_entry.id,
        template_types=[template_type],
        templates=[template_entry],
    )
    fake_store = FakeSessionStore()
    fake_store.last_session = last_session
    window, _fake_store, _main_window_module = main_window_factory(fake_store=fake_store)

    assert window.current_project_path == str(project_dir.resolve())
    assert window.session.template_path == str(template_path.resolve())
    assert_stage_state(window, 2, blocked=False)


def test_theme_toggle_debounces_last_session_persistence(main_window_factory):
    window, fake_store, _main_window_module = main_window_factory()
    assert fake_store.session is None

    window._toggle_theme()

    assert window._theme_persist_timer.isActive() is True
    assert fake_store.session is None

    with patch.object(window._last_session_persistence, "enqueue") as enqueue:
        window._flush_theme_session_persist()

    enqueue.assert_called_once()
    persisted_snapshot = enqueue.call_args.args[0]
    assert persisted_snapshot.theme_mode == window.session.theme_mode


def test_close_event_flushes_pending_last_session_snapshot(main_window_factory):
    window, fake_store, _main_window_module = main_window_factory()
    assert fake_store.session is None

    window._toggle_theme()
    with patch.object(window, "_confirm_close_action", return_value="save"), patch.object(
        window,
        "_save_project",
        return_value=True,
    ):
        window.close()

    assert fake_store.session is not None
    assert fake_store.session.theme_mode == window.session.theme_mode

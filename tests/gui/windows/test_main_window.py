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
from core.enums.app_themes import AppTheme
from core.manager.theme_manager import ThemeManager
from tests.helpers.gui import assert_stage_state, mapping_combo


class FakeProjectOpenDialog:
    next_selected_path = ""
    next_result = QDialog.DialogCode.Accepted
    instances = []

    def __init__(self, *_args, **_kwargs):
        self.selected_path = self.__class__.next_selected_path
        self.result = self.__class__.next_result
        self.__class__.instances.append(self)

    def setAcceptMode(self, *_args):
        return None

    def setFileMode(self, *_args):
        return None

    def setOption(self, *_args):
        return None

    def setFilter(self, *_args):
        return None

    def setNameFilter(self, *_args):
        return None

    def selectFile(self, *_args):
        return None

    def exec(self):
        return self.result

    def selectedFiles(self):
        return [self.selected_path] if self.selected_path else []

    @classmethod
    def reset(cls):
        cls.next_selected_path = ""
        cls.next_result = QDialog.DialogCode.Accepted
        cls.instances = []


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
    assert window.setup_page.template_override_input["input"].text() == str(prepared_window.files.template)

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

    with patch.object(window, "_confirm_new_project_action", return_value="discard"):
        window._new_project()
    assert window.stage_manager.currentIndex() == 0
    assert window.document.is_dirty is True
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
    project_dir = temp_dir / "portable-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.json").write_text("{}", encoding="utf-8")
    FakeProjectOpenDialog.reset()
    FakeProjectOpenDialog.next_selected_path = str(project_dir)
    with patch.object(main_window_module, "QFileDialog", FakeProjectOpenDialog):
        window._open_project()

    assert window.stage_manager.currentIndex() == 0
    assert window.current_project_path == str(project_dir.resolve())
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)
    assert_stage_state(window, 3, active=False, blocked=False, completed=False)
    assert_stage_state(window, 4, active=False, blocked=True, completed=False)
    assert window.template_type_combo.currentText() == "Default template"
    assert window.template_combo.currentText() == "Default template 01"


def test_open_project_uses_a_single_dialog_instance(main_window_factory, tmp_path):
    window, fake_store, main_window_module = main_window_factory()
    fake_store.loaded_session = ProjectSession()
    project_dir = tmp_path / "portable-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.json").write_text("{}", encoding="utf-8")

    FakeProjectOpenDialog.reset()
    FakeProjectOpenDialog.next_selected_path = str(project_dir)
    with patch.object(main_window_module, "QFileDialog", FakeProjectOpenDialog):
        window._open_project()

    assert len(FakeProjectOpenDialog.instances) == 1


def test_open_project_accepts_project_json_for_compatibility(main_window_factory, tmp_path):
    window, fake_store, main_window_module = main_window_factory()
    fake_store.loaded_session = ProjectSession()
    project_dir = tmp_path / "portable-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    manifest = project_dir / "project.json"
    manifest.write_text("{}", encoding="utf-8")

    FakeProjectOpenDialog.reset()
    FakeProjectOpenDialog.next_selected_path = str(manifest)
    with patch.object(main_window_module, "QFileDialog", FakeProjectOpenDialog):
        window._open_project()

    assert window.current_project_path == str(project_dir.resolve())


def test_new_project_confirmation_cancel_keeps_current_session(prepared_window):
    window = prepared_window.window
    original_session = window.session.clone()

    with patch.object(window, "_confirm_new_project_action", return_value=None):
        window._new_project()

    assert window.session.to_dict() == original_session.to_dict()


def test_new_project_confirmation_save_current_creates_empty_project(prepared_window):
    window = prepared_window.window

    with patch.object(window, "_confirm_new_project_action", return_value="save_current"), patch.object(
        window,
        "_save_project",
        return_value=True,
    ) as save_project:
        window._new_project()

    save_project.assert_called_once()
    assert window.current_project_path is None
    assert window.session.excel_path == ""
    assert window.session.output_dir == ""
    assert window.template_type_combo.currentText() == "Default template"
    assert window.template_combo.currentText() == "Default template 01"


def test_new_project_confirmation_save_copy_creates_unsaved_copy(prepared_window):
    window = prepared_window.window

    _unlock_generate_stage(window)
    original_session = window.session.clone()

    with patch.object(window, "_confirm_new_project_action", return_value="save_copy"), patch.object(
        window,
        "_save_project",
        return_value=True,
    ) as save_project:
        window._new_project()

    save_project.assert_called_once()
    assert window.current_project_path is None
    assert window.session.excel_path == original_session.excel_path
    assert window.session.output_dir == original_session.output_dir
    assert window.session.output_naming_schema == original_session.output_naming_schema
    assert window.session.mappings == original_session.mappings


def test_theme_toggle_persists_on_project_and_new_project_resets_to_config(prepared_window):
    window = prepared_window.window
    original_theme = window.default_theme_mode

    window._toggle_theme()

    assert window.session.theme_mode != original_theme

    with patch.object(window, "_confirm_new_project_action", return_value="discard"):
        window._new_project()

    assert window.session.theme_mode == window.default_theme_mode
    assert ThemeManager.get_current_theme().name == window.default_theme_mode


def test_open_project_applies_saved_project_theme(prepared_window):
    window = prepared_window.window
    fake_store = prepared_window.fake_store
    main_window_module = prepared_window.main_window_module
    target_theme = AppTheme.LIGHT if ThemeManager.get_current_theme() != AppTheme.LIGHT else AppTheme.DARK

    fake_store.loaded_session = ProjectSession(theme_mode=target_theme.name)

    project_dir = prepared_window.files.root / "portable-theme-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.json").write_text("{}", encoding="utf-8")
    FakeProjectOpenDialog.reset()
    FakeProjectOpenDialog.next_selected_path = str(project_dir)
    with patch.object(main_window_module, "QFileDialog", FakeProjectOpenDialog):
        window._open_project()

    assert window.session.theme_mode == target_theme.name
    assert ThemeManager.get_current_theme() == target_theme


def test_open_project_rejects_folder_without_project_manifest(main_window_factory, tmp_path):
    window, fake_store, main_window_module = main_window_factory()
    fake_store.loaded_session = ProjectSession()
    invalid_project_dir = tmp_path / "empty-project"
    invalid_project_dir.mkdir(parents=True, exist_ok=True)

    FakeProjectOpenDialog.reset()
    FakeProjectOpenDialog.next_selected_path = str(invalid_project_dir)
    with patch.object(main_window_module, "QFileDialog", FakeProjectOpenDialog), patch.object(
        main_window_module.QMessageBox,
        "critical",
    ) as critical:
        window._open_project()

    critical.assert_called_once()
    assert "project.json" in critical.call_args.args[2]


def test_open_project_rejects_non_manifest_file(main_window_factory, tmp_path):
    window, fake_store, main_window_module = main_window_factory()
    fake_store.loaded_session = ProjectSession()
    invalid_file = tmp_path / "notes.json"
    invalid_file.write_text("{}", encoding="utf-8")

    FakeProjectOpenDialog.reset()
    FakeProjectOpenDialog.next_selected_path = str(invalid_file)
    with patch.object(main_window_module, "QFileDialog", FakeProjectOpenDialog), patch.object(
        main_window_module.QMessageBox,
        "critical",
    ) as critical:
        window._open_project()

    critical.assert_called_once()
    assert "project.json" in critical.call_args.args[2]


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
    window.close()

    assert fake_store.session is not None
    assert fake_store.session.theme_mode == window.session.theme_mode

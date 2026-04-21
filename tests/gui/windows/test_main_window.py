from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox

from core.mapping.models import (
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


def test_fresh_start_has_empty_inputs_and_no_templates(main_window_factory):
    window, _store, _main_window_module = main_window_factory()

    assert window.setup_page.excel_input["input"].text() == ""
    assert window.setup_page.output_input["input"].text() == ""
    assert window.setup_page.template_override_input["input"].text() == ""
    assert window.session.template_types == []
    assert window.session.templates == []
    assert window.session.selected_template_type == ""
    assert window.session.selected_template == ""
    assert window.template_type_combo.count() == 1
    assert window.template_type_combo.currentData() == ""
    assert window.template_combo.count() == 1
    assert window.template_combo.currentData() == ""


def _result_with_existing_outputs(
    root_dir: Path,
    *,
    include_pdf: bool = False,
    errors: list[str] | None = None,
) -> GenerationResult:
    docx_dir = root_dir / "docx"
    docx_dir.mkdir(parents=True, exist_ok=True)
    docx_path = docx_dir / "ADA_attestato_certificato.docx"
    docx_path.write_text("docx", encoding="utf-8")

    pdf_paths: list[str] = []
    if include_pdf:
        pdf_dir = root_dir / "pdf"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = pdf_dir / "ADA_attestato_certificato.pdf"
        pdf_path.write_text("pdf", encoding="utf-8")
        pdf_paths = [str(pdf_path)]

    return GenerationResult(
        total_rows=1,
        success_count=1,
        generated_docx_paths=[str(docx_path)],
        generated_pdf_paths=pdf_paths,
        log_path=str(root_dir / "generation.log"),
        errors=errors or [],
    )


def test_workflow_rail_stays_synced_with_real_stage_state(prepared_window):
    window = prepared_window.window

    assert len(window.stage_cards) == 5
    assert window.sidebar_title.text() == "Workflow"
    assert window.template_toolbar.isHidden() is False
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)
    assert_stage_state(window, 2, active=False, blocked=False, completed=False)
    assert_stage_state(window, 3, active=False, blocked=True, completed=False)
    assert_stage_state(window, 4, active=False, blocked=True, completed=False)
    assert_stage_state(window, 5, active=False, blocked=True, completed=False)

    window.stage_manager.setCurrentIndex(2)
    assert window.stage_manager.currentIndex() == 0
    assert_stage_state(window, 1, active=True, blocked=False, completed=False)

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
    window.stage_cards[5].clicked.emit(5)
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
        log_path=str(Path(temp_dir) / "generation.log"),
        errors=[],
    )
    window._handle_generation_result(result)

    assert window.stage_manager.currentIndex() == 3
    assert "Created 1 of 1 DOCX documents." in window.results_page.summary_label.text()
    assert window.results_page.errors_box.isHidden() is True
    assert window.results_page.files_view_stack.currentWidget() == window.results_page.single_files_page
    assert window.results_page.files_list.count() == 1
    file_entry = window.results_page.files_list.itemWidget(window.results_page.files_list.item(0))
    assert file_entry is not None
    assert file_entry.open_button.text() == "Open"
    assert_stage_state(window, 3, completed=True)
    assert_stage_state(window, 4, active=True, blocked=False)
    assert_stage_state(window, 5, active=False, blocked=False)

    window.localization.set_language("it")

    assert window.view_menu.title() == "Visualizza"
    assert hasattr(window.setup_page, "next_button") is False
    assert "esempio" in window.mapping_page.mapping_hint.text()
    assert window.mapping_page.output_naming_schema_label.text() == "Schema nome output"
    assert window.template_type_label.text() == "Tipo template"
    file_entry = window.results_page.files_list.itemWidget(window.results_page.files_list.item(0))
    assert file_entry.open_button.text() == "Apri"
    assert "Creati 1 documenti DOCX su 1." in window.results_page.summary_label.text()
    assert_stage_state(window, 4, active=True, blocked=False)
    assert_stage_state(window, 5, active=False, blocked=False)


def test_results_page_splits_docx_and_pdf_outputs(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)

    result = GenerationResult(
        total_rows=1,
        success_count=1,
        generated_docx_paths=[str(Path(temp_dir) / "docx" / "ADA_attestato_certificato.docx")],
        generated_pdf_paths=[str(Path(temp_dir) / "pdf" / "ADA_attestato_certificato.pdf")],
        log_path=str(Path(temp_dir) / "generation.log"),
        errors=[],
    )
    window._handle_generation_result(result)

    assert window.results_page.files_view_stack.currentWidget() == window.results_page.split_files_page
    assert window.results_page.docx_files_list.count() == 1
    assert window.results_page.pdf_files_list.count() == 1
    docx_entry = window.results_page.docx_files_list.itemWidget(window.results_page.docx_files_list.item(0))
    pdf_entry = window.results_page.pdf_files_list.itemWidget(window.results_page.pdf_files_list.item(0))
    assert docx_entry is not None
    assert pdf_entry is not None
    assert docx_entry.open_button.text() == "Open"
    assert pdf_entry.open_button.text() == "Open"


def test_archive_page_shows_archive_controls(prepared_window):
    window = prepared_window.window

    assert window.archive_page.archive_root_label.isHidden() is False
    assert window.archive_page.archive_root_input.isHidden() is False
    assert window.archive_page.archive_root_browse_button.isHidden() is False
    assert window.archive_page.archive_run_name_label.isHidden() is False
    assert window.archive_page.archive_run_name_input.isHidden() is False
    assert window.archive_page.archive_format_label.isHidden() is False
    assert window.archive_page.archive_format_combo.isHidden() is False
    assert window.archive_page.archive_output_button.isHidden() is False
    assert window.archive_page.open_archive_button.isHidden() is False


def test_archive_page_defaults_format_to_folder(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)
    result = _result_with_existing_outputs(Path(temp_dir), include_pdf=True)
    window._handle_generation_result(result)
    window.stage_cards[5].clicked.emit(5)

    assert window.archive_page.archive_format_combo.currentData() == "folder"


def test_archive_page_archive_output_creates_zip_and_enables_open(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)
    result = _result_with_existing_outputs(Path(temp_dir), include_pdf=True)
    window._handle_generation_result(result)
    window.stage_cards[5].clicked.emit(5)

    archive_root = Path(temp_dir) / "archives"
    window.archive_page.archive_root_input.setText(str(archive_root))
    window.archive_page.archive_run_name_input.setText("run 01")
    format_index = window.archive_page.archive_format_combo.findData("zip")
    if format_index >= 0:
        window.archive_page.archive_format_combo.setCurrentIndex(format_index)

    with patch("gui.workflow.archive_page.QMessageBox.information") as info_mock:
        window.archive_page.archive_output_button.click()

    archive_path = archive_root / "run_01.zip"
    assert archive_path.exists()
    assert window.archive_page.open_archive_button.isEnabled() is True
    info_mock.assert_called_once()

    with patch("gui.workflow.archive_page.open_path") as open_path_mock:
        window.archive_page.open_archive_button.click()
    open_path_mock.assert_called_once_with(str(archive_path))


def test_archive_page_archive_output_prompts_before_overwrite(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)
    result = _result_with_existing_outputs(Path(temp_dir), include_pdf=False)
    window._handle_generation_result(result)
    window.stage_cards[5].clicked.emit(5)

    archive_root = Path(temp_dir) / "archives"
    window.archive_page.archive_root_input.setText(str(archive_root))
    window.archive_page.archive_run_name_input.setText("run 01")
    format_index = window.archive_page.archive_format_combo.findData("zip")
    if format_index >= 0:
        window.archive_page.archive_format_combo.setCurrentIndex(format_index)

    with patch("gui.workflow.archive_page.QMessageBox.information"):
        window.archive_page.archive_output_button.click()

    with patch(
        "gui.workflow.archive_page.QMessageBox.question",
        return_value=QMessageBox.StandardButton.Yes,
    ) as question_mock, patch("gui.workflow.archive_page.QMessageBox.information") as info_mock:
        window.archive_page.archive_output_button.click()

    question_mock.assert_called_once()
    info_mock.assert_called_once()


def test_archive_page_archive_action_is_disabled_for_runs_with_errors(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)
    result = _result_with_existing_outputs(Path(temp_dir), include_pdf=False, errors=["Row 1 failed"])
    window._handle_generation_result(result)
    window.stage_cards[5].clicked.emit(5)

    assert window.archive_page.archive_output_button.isEnabled() is False


def test_archive_page_prefills_root_and_keeps_run_name_empty_on_new_result(prepared_window):
    window = prepared_window.window
    temp_dir = prepared_window.files.root

    _unlock_generate_stage(window)
    result = _result_with_existing_outputs(Path(temp_dir), include_pdf=True)
    window._handle_generation_result(result)
    window.stage_cards[5].clicked.emit(5)

    assert window.archive_page.archive_root_input.text() == str(temp_dir)
    assert window.archive_page.archive_run_name_input.text() == ""


def test_generate_page_prompts_before_clearing_session_output_cache(prepared_window):
    window = prepared_window.window
    temp_dir = Path(prepared_window.files.root)

    _unlock_generate_stage(window)
    window.stage_cards[3].clicked.emit(3)
    window.generate_page._has_generated_in_app_session = True

    cached_docx_dir = temp_dir / "docx"
    cached_docx_dir.mkdir(parents=True, exist_ok=True)
    (cached_docx_dir / "ADA.docx").write_text("cached", encoding="utf-8")

    with patch(
        "gui.workflow.generate_page.QMessageBox.question",
        return_value=QMessageBox.StandardButton.No,
    ) as question_mock:
        window.generate_page._start_generation()

    question_mock.assert_called_once()
    assert window.generate_page._thread is None


def test_generate_page_output_cache_helpers_detect_and_clear_artifacts(prepared_window):
    window = prepared_window.window
    temp_dir = Path(prepared_window.files.root)
    output_dir = str(temp_dir)

    docx_dir = temp_dir / "docx"
    pdf_dir = temp_dir / "pdf"
    docx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)
    (docx_dir / "ADA.docx").write_text("docx", encoding="utf-8")
    (pdf_dir / "ADA.pdf").write_text("pdf", encoding="utf-8")
    (temp_dir / "generation.log").write_text("log", encoding="utf-8")

    assert window.generate_page._has_output_cache(output_dir) is True

    window.generate_page._clear_output_cache(output_dir)

    assert (temp_dir / "docx").exists() is False
    assert (temp_dir / "pdf").exists() is False
    assert (temp_dir / "generation.log").exists() is False
    assert window.generate_page._has_output_cache(output_dir) is False


def test_generate_page_output_cache_helpers_include_legacy_log(prepared_window):
    window = prepared_window.window
    temp_dir = Path(prepared_window.files.root)
    output_dir = str(temp_dir)

    legacy_log = temp_dir / "certificate_generation.log"
    legacy_log.write_text("legacy", encoding="utf-8")

    assert window.generate_page._has_output_cache(output_dir) is True
    window.generate_page._clear_output_cache(output_dir)
    assert legacy_log.exists() is False


def test_generate_page_cache_artifacts_handles_invalid_output_dir(prepared_window):
    window = prepared_window.window

    assert window.generate_page._cache_artifacts("\0") == []
    assert window.generate_page._has_output_cache("\0") is False


def test_generate_page_marks_session_as_generated_only_when_files_exist(prepared_window):
    window = prepared_window.window

    assert window.generate_page._has_generated_in_app_session is False

    window.generate_page._handle_finished(
        GenerationResult(
            total_rows=1,
            success_count=1,
            generated_docx_paths=["/tmp/fake.docx"],
            generated_pdf_paths=[],
            log_path="",
            errors=[],
        )
    )
    assert window.generate_page._has_generated_in_app_session is True


def test_generate_page_does_not_mark_session_generated_for_empty_result(prepared_window):
    window = prepared_window.window

    window.generate_page._has_generated_in_app_session = False
    window.generate_page._handle_finished(GenerationResult())

    assert window.generate_page._has_generated_in_app_session is False


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


def test_close_event_requests_generate_page_shutdown(main_window_factory):
    window, _fake_store, _main_window_module = main_window_factory()

    with patch.object(window, "_confirm_close_action", return_value="discard"), patch.object(
        window.generate_page,
        "shutdown",
        return_value=True,
    ) as shutdown_mock:
        window.close()

    shutdown_mock.assert_called_once_with(window.GENERATION_SHUTDOWN_TIMEOUT_MILLISECONDS)


def test_close_event_marks_force_process_exit_when_generation_does_not_stop(main_window_factory):
    window, _fake_store, _main_window_module = main_window_factory()
    app = QApplication.instance()
    assert app is not None
    app.setProperty(window.FORCE_PROCESS_EXIT_PROPERTY, False)

    with patch.object(window, "_confirm_close_action", return_value="discard"), patch.object(
        window.generate_page,
        "shutdown",
        return_value=False,
    ):
        window.close()

    assert bool(app.property(window.FORCE_PROCESS_EXIT_PROPERTY)) is True


def test_about_popup_includes_version_and_author(prepared_window):
    window = prepared_window.window
    window.config["APP_VERSION"] = "9.9.1"
    window.config["APP_AUTHOR"] = "QA Team"

    with patch("gui.windows.main_window.QMessageBox.information") as info_mock:
        window._show_about()

    info_mock.assert_called_once()
    body = info_mock.call_args.args[2]
    assert "Version: 9.9.1" in body
    assert "Author: QA Team" in body

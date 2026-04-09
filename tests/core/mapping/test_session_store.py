from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from core.mapping.models import MappingEntry, ProjectSession, ProjectTemplateEntry, ProjectTemplateType
from core.mapping.session_store import ProjectSessionStore
from core.util.app_paths import AppPaths


def test_session_store_round_trip(tmp_path):
    source_template = tmp_path / "source_template.docx"
    source_template.write_text("Hello <<NAME>>", encoding="utf-8")
    template_entry = ProjectTemplateEntry(
        display_name="attestato",
        type_name="General",
        source_path=str(source_template),
        is_managed=False,
    )
    session = ProjectSession(
        excel_path="/tmp/data.xlsx",
        output_dir="/tmp/out",
        archive_root_dir="/tmp/archive-root",
        theme_mode="DARK",
        selected_template_type="General",
        selected_template=template_entry.id,
        template_types=[ProjectTemplateType("General")],
        templates=[template_entry],
        output_naming_schema="{COGNOME}_{ROW}",
        placeholder_delimiter="{{",
        export_pdf=True,
        mappings=[MappingEntry(placeholder="<<NAME>>", column_name="NOME")],
    )

    store = ProjectSessionStore(tmp_path)
    project_dir = tmp_path / "project"
    saved_path = store.save(session, project_dir)
    loaded = store.load(project_dir)
    saved_payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert saved_path == project_dir / "project.json"
    assert saved_payload["excel_path"] == "/tmp/data.xlsx"
    assert saved_payload["output_dir"] == "/tmp/out"
    assert saved_payload["archive_root_dir"] == "/tmp/archive-root"
    assert saved_payload["template_override_path"] == ""
    assert saved_payload["license_path"] == ""
    assert saved_payload["templates"][0]["relative_path"].startswith("templates/")
    assert "source_path" not in saved_payload["templates"][0]
    assert loaded.selected_template_type == "General"
    assert loaded.selected_template_entry() is not None
    assert loaded.selected_template_entry().is_managed is True
    assert Path(loaded.template_path).exists()
    assert loaded.excel_path == "/tmp/data.xlsx"
    assert loaded.output_dir == "/tmp/out"
    assert loaded.archive_root_dir == "/tmp/archive-root"
    assert loaded.template_override_path == ""
    assert loaded.output_naming_schema == "{COGNOME}_{ROW}"
    assert loaded.placeholder_delimiter == "{{"
    assert loaded.theme_mode == "DARK"


def test_session_store_loads_legacy_files(tmp_path):
    store = ProjectSessionStore(tmp_path)
    config_path = tmp_path / "config.json"
    setup_path = tmp_path / "SETUP.json"

    config_path.write_text(
        '{"<<NOME>>": "NOME", "<<COGNOME>>": "COGNOME"}',
        encoding="utf-8",
    )
    setup_path.write_text(
        (
            "{"
            '"excel_path": "/tmp/data.xlsx", '
            '"template_path": "/tmp/template.docx", '
            '"output_dir": "/tmp/out", '
            '"license_path": "/tmp/license.xml", '
            '"toPDF": true, '
            '"toPDF_timeout": 180'
            "}"
        ),
        encoding="utf-8",
    )

    session = store.load_legacy_files(config_path, setup_path)

    assert session.excel_path == "/tmp/data.xlsx"
    assert session.template_path == "/tmp/template.docx"
    assert session.output_dir == "/tmp/out"
    assert session.license_path == "/tmp/license.xml"
    assert session.selected_template_type == "Default template"
    assert session.selected_template_entry() is not None
    assert session.selected_template_entry().label == "Default template 01"
    assert session.placeholder_delimiter == "<<"
    assert session.placeholder_start == "<<"
    assert session.placeholder_end == ">>"
    assert session.export_pdf is True
    assert session.pdf_timeout_seconds == 180
    assert len(session.mappings) == 2
    assert session.mappings[0].placeholder == "<<NOME>>"
    assert session.mappings[0].column_name == "NOME"


def test_session_store_migrates_legacy_last_session_into_state_dir(tmp_path):
    state_dir = tmp_path / "state"
    legacy_dir = tmp_path / "legacy"
    state_dir.mkdir(parents=True, exist_ok=True)
    legacy_dir.mkdir(parents=True, exist_ok=True)
    legacy_path = legacy_dir / "last_session.json"
    legacy_path.write_text(
        '{"excel_path": "/tmp/data.xlsx", "output_naming_schema": "{ROW}"}',
        encoding="utf-8",
    )

    with patch.object(AppPaths, "state_dir", return_value=state_dir), patch.object(
        AppPaths,
        "legacy_last_session_path",
        return_value=legacy_path,
    ):
        store = ProjectSessionStore()
        loaded = store.load_last_session()

    assert store.last_session_path.parent == state_dir
    assert loaded.excel_path == "/tmp/data.xlsx"
    assert legacy_path.exists() is False
    assert store.last_session_path.exists() is True


def test_session_store_quarantines_invalid_last_session(tmp_path):
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    last_session_path = state_dir / "last_session.json"
    last_session_path.write_text("{invalid", encoding="utf-8")
    legacy_path = tmp_path / "missing_legacy.json"

    with patch.object(AppPaths, "state_dir", return_value=state_dir), patch.object(
        AppPaths,
        "legacy_last_session_path",
        return_value=legacy_path,
    ):
        store = ProjectSessionStore()
        loaded = store.load_last_session()

    assert loaded.to_dict() == ProjectSession().to_dict()
    assert last_session_path.exists() is False
    assert len(list(state_dir.glob("last_session.invalid-*.json"))) == 1


def test_last_session_round_trip_preserves_local_machine_paths(tmp_path):
    store = ProjectSessionStore(tmp_path)
    session = ProjectSession(
        excel_path="/tmp/data.xlsx",
        output_dir="/tmp/out",
        archive_root_dir="/tmp/archive-root",
        template_override_path="/tmp/override.docx",
        license_path="/tmp/license.xml",
    )

    store.save_last_session(session)
    loaded = store.load_last_session()

    assert loaded.excel_path == "/tmp/data.xlsx"
    assert loaded.output_dir == "/tmp/out"
    assert loaded.archive_root_dir == "/tmp/archive-root"
    assert loaded.template_override_path == "/tmp/override.docx"
    assert loaded.license_path == "/tmp/license.xml"


def test_session_store_save_as_copies_existing_managed_templates_from_source_project(tmp_path):
    source_project_dir = tmp_path / "source-project"
    source_templates_dir = source_project_dir / "templates"
    source_templates_dir.mkdir(parents=True, exist_ok=True)
    managed_template = source_templates_dir / "Default_template_01.docx"
    managed_template.write_text("Hello <NAME>", encoding="utf-8")

    template_entry = ProjectTemplateEntry(
        display_name="Default template 01",
        type_name="Default template",
        relative_path="templates/Default_template_01.docx",
        is_managed=True,
    )
    session = ProjectSession(
        selected_template_type="Default template",
        selected_template=template_entry.id,
        template_types=[ProjectTemplateType("Default template")],
        templates=[template_entry],
        mappings=[MappingEntry(placeholder="<NAME>", column_name="NAME")],
    )

    store = ProjectSessionStore(tmp_path)
    target_project_dir = tmp_path / "shared-project-copy"
    saved_path = store.save(session, target_project_dir, source_project_dir=source_project_dir)
    saved_payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert (target_project_dir / "templates" / "Default_template_01.docx").exists()
    assert saved_payload["templates"][0]["relative_path"] == "templates/Default_template_01.docx"
    assert "source_path" not in saved_payload["templates"][0]

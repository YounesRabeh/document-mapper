from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from core.certificate.models import MappingEntry, ProjectSession
from core.certificate.session_store import ProjectSessionStore
from core.util.app_paths import AppPaths


def test_session_store_round_trip(tmp_path):
    session = ProjectSession(
        excel_path="/tmp/data.xlsx",
        template_path="/tmp/template.docx",
        output_dir="/tmp/out",
        certificate_type="attestato",
        output_naming_schema="{COGNOME}_{ROW}",
        placeholder_delimiter="{{",
        export_pdf=True,
        mappings=[MappingEntry(placeholder="<<NAME>>", column_name="NOME")],
    )

    store = ProjectSessionStore(tmp_path)
    saved_path = store.save(session, tmp_path / "project.json")
    loaded = store.load(saved_path)

    assert loaded.to_dict() == session.to_dict()


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
            '"certificate_type": "attestato", '
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
    assert session.certificate_type == "attestato"
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

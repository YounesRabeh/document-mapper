from __future__ import annotations

from core.certificate.models import ProjectSession
from core.project import ProjectDocument


def test_project_document_tracks_persisted_project_fields_in_snapshot():
    document = ProjectDocument(session=ProjectSession())

    assert document.is_dirty is False

    document.session.excel_path = "/tmp/data.xlsx"
    assert document.is_dirty is True

    document.session.excel_path = ""
    assert document.is_dirty is False

    document.session.output_dir = "/tmp/out"
    assert document.is_dirty is True

    document.session.output_dir = ""
    assert document.is_dirty is False

    document.session.output_naming_schema = "{ROW}"
    assert document.is_dirty is True


def test_project_document_returns_clean_when_changes_revert_to_saved_snapshot():
    session = ProjectSession(output_naming_schema="{NAME}_{LASTNAME}")
    document = ProjectDocument(session=session)

    document.session.output_naming_schema = "{NAME}_{LASTNAME}_{ROW}"
    assert document.is_dirty is True

    document.session.output_naming_schema = "{NAME}_{LASTNAME}"
    assert document.is_dirty is False


def test_project_document_load_and_activate_reset_or_preserve_saved_state():
    loaded = ProjectSession(excel_path="/tmp/workbook.xlsx")
    document = ProjectDocument(session=ProjectSession())

    document.load(loaded, "/tmp/project")
    assert document.project_dir is not None
    assert document.project_dir.name == "project"
    assert document.is_dirty is False

    document.activate(ProjectSession(output_dir="/tmp/out"), None, saved=False)
    assert document.project_dir is None
    assert document.is_dirty is True

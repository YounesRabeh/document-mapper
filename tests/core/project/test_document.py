from __future__ import annotations

from core.certificate.models import ProjectSession
from core.project import ProjectDocument


def test_project_document_tracks_dirty_state_from_session_snapshot():
    document = ProjectDocument(session=ProjectSession())

    assert document.is_dirty is False

    document.session.excel_path = "/tmp/data.xlsx"
    assert document.is_dirty is True

    document.mark_saved()
    assert document.is_dirty is False

    document.session.output_dir = "/tmp/out"
    assert document.is_dirty is True


def test_project_document_returns_clean_when_changes_revert_to_saved_snapshot():
    session = ProjectSession(excel_path="/tmp/data.xlsx", output_dir="/tmp/out")
    document = ProjectDocument(session=session)

    document.session.output_dir = "/tmp/new-out"
    assert document.is_dirty is True

    document.session.output_dir = "/tmp/out"
    assert document.is_dirty is False

    document.mark_unsaved()
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

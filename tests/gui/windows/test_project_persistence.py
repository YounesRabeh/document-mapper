from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_save_project_defaults_to_documents_path(main_window_factory, tmp_path):
    window, _fake_store, main_window_module = main_window_factory()
    internal_project_dir = tmp_path / "state" / "document-mapper-project"

    with patch.object(main_window_module.AppPaths, "internal_project_dir", return_value=internal_project_dir):
        assert window._save_project() is True

    assert window.current_project_path == str(internal_project_dir.resolve())
    assert (internal_project_dir / "project.json").exists()


def test_save_project_keeps_current_project_path_as_directory(main_window_factory, tmp_path):
    window, _fake_store, _main_window_module = main_window_factory()
    project_dir = tmp_path / "portable-project"
    window.session.excel_path = "/tmp/data.xlsx"
    window.session.output_dir = "/tmp/out"

    assert window._save_project_to_path(project_dir) is True
    assert window.current_project_path == str(project_dir.resolve())
    assert window.session.excel_path == "/tmp/data.xlsx"
    assert window.session.output_dir == "/tmp/out"


def test_save_project_as_uses_same_internal_app_project_directory(main_window_factory, tmp_path):
    window, _fake_store, main_window_module = main_window_factory()
    internal_project_dir = tmp_path / "state" / "document-mapper-project"

    with patch.object(main_window_module.AppPaths, "internal_project_dir", return_value=internal_project_dir):
        assert window._save_project_as() is True

    assert window.current_project_path == str(internal_project_dir.resolve())
    assert (internal_project_dir / "project.json").exists()

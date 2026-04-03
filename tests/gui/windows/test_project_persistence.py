from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_save_project_defaults_to_documents_path(main_window_factory, tmp_path):
    window, _fake_store, main_window_module = main_window_factory()
    default_project_path = tmp_path / "Documents" / "document-mapper-project"
    default_project_path.mkdir(parents=True, exist_ok=True)

    with patch.object(main_window_module.AppPaths, "default_project_path", return_value=default_project_path), patch.object(
        main_window_module.QFileDialog,
        "getExistingDirectory",
        return_value="",
    ) as save_dialog:
        window._save_project_as()

    assert save_dialog.call_args.args[2] == str(default_project_path)


def test_save_project_keeps_current_project_path_as_directory(main_window_factory, tmp_path):
    window, _fake_store, _main_window_module = main_window_factory()
    project_dir = tmp_path / "portable-project"

    assert window._save_project_to_path(project_dir) is True
    assert window.current_project_path == str(project_dir.resolve())

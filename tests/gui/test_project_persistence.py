from __future__ import annotations

from pathlib import Path
from unittest.mock import patch


def test_save_project_defaults_to_documents_path(main_window_factory, tmp_path):
    window, _fake_store, main_window_module = main_window_factory()
    default_project_path = tmp_path / "Documents" / "document-mapper-project.json"
    default_project_path.parent.mkdir(parents=True, exist_ok=True)

    with patch.object(main_window_module.AppPaths, "default_project_path", return_value=default_project_path), patch.object(
        main_window_module.QFileDialog,
        "getSaveFileName",
        return_value=("", ""),
    ) as save_dialog:
        window._save_project_as()

    assert save_dialog.call_args.args[2] == str(default_project_path)

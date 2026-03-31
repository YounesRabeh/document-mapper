from __future__ import annotations

from pathlib import Path

from core.config.environment_setup import EnvironmentSetup
from core.util.app_paths import AppPaths
from core.util.resources import Resources


def test_environment_setup_uses_project_root_not_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    setup = EnvironmentSetup()

    assert setup.project_root == AppPaths.project_root()
    assert setup.toml_path.exists()


def test_resources_resolve_from_project_root_not_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    Resources.initialize(
        {
            "RESOURCES_BASE": "resources",
            "RESOURCES_QSS": "resources/qss",
            "RESOURCES_ICONS": "resources/icons",
            "RESOURCES_IMAGES": "resources/images",
            "RESOURCES_FONTS": "resources/fonts",
        }
    )
    qss_path = Path(Resources.get_in_qss("elements/file_entry/default.qss"))

    assert qss_path.exists()
    assert str(qss_path).startswith(str(AppPaths.project_root()))

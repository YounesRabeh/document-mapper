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
        }
    )
    icon_path = Path(Resources.get_in_icons("sys/chevron_down.svg"))

    assert icon_path.exists()
    assert str(icon_path).startswith(str(AppPaths.project_root()))


def test_locales_and_qss_resolve_from_resources():
    locales_dir = AppPaths.locales_dir()
    qss_dir = AppPaths.resource_root("resources") / "qss"

    assert locales_dir is not None
    assert (locales_dir / "en.json").exists()
    assert (locales_dir / "it.json").exists()
    assert (qss_dir / "main_window.qss").exists()
    assert (qss_dir / "workflow_page.qss").exists()
    assert (qss_dir / "template_manager_dialog.qss").exists()


def test_legacy_gui_ui_factory_stack_is_removed():
    assert not (AppPaths.project_root() / "gui" / "ui" / "ui_factory.py").exists()
    assert not (AppPaths.project_root() / "gui" / "ui" / "elements" / "drag_drop.py").exists()
    assert not (AppPaths.project_root() / "gui" / "ui" / "elements" / "file_entry.py").exists()
    assert not (AppPaths.project_root() / "gui" / "ui" / "elements" / "menu_bar.py").exists()


def test_inline_python_qss_modules_are_removed():
    assert not (AppPaths.project_root() / "gui" / "styles" / "main_window.py").exists()
    assert not (AppPaths.project_root() / "gui" / "styles" / "workflow.py").exists()


def test_generated_ui_python_files_exist_only_in_gui_forms():
    project_root = AppPaths.project_root()
    generated_files = sorted(project_root.rglob("ui_*.py"))
    expected_files = sorted((project_root / "gui" / "forms").glob("ui_*.py"))

    assert generated_files == expected_files
    assert expected_files

    for generated in expected_files:
        source_ui = generated.with_name(generated.name.removeprefix("ui_")).with_suffix(".ui")
        assert source_ui.exists(), f"Missing .ui source for generated form: {generated}"

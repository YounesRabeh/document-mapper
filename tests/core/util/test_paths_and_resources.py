from __future__ import annotations

from pathlib import Path

import core.util.app_icon as app_icon_module
from core.config.environment_setup import EnvironmentSetup
from core.util.app_icon import (
    ApplicationIntegrationTarget,
    DESKTOP_ENTRY_FILENAME,
    DESKTOP_FILE_NAME,
    build_application_identifier,
    configure_qt_application_identity,
    detect_application_integration,
    resolve_app_icon_path,
)
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


def test_generated_ui_python_files_exist_only_in_gui_forms():
    project_root = AppPaths.project_root()
    generated_files = sorted(project_root.rglob("ui_*.py"))
    expected_files = sorted((project_root / "gui" / "forms").glob("ui_*.py"))

    assert generated_files == expected_files
    assert expected_files

    for generated in expected_files:
        source_ui = generated.with_name(generated.name.removeprefix("ui_")).with_suffix(".ui")
        assert source_ui.exists(), f"Missing .ui source for generated form: {generated}"


def test_environment_setup_ignores_unrelated_uppercase_env_vars(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("APP_LANGUAGE=en\n", encoding="utf-8")
    unrelated_dir = tmp_path / "should_not_be_created"
    monkeypatch.setenv("DOCUMENT_MAPPER_TEST_RANDOM_DIR", str(unrelated_dir))

    setup = EnvironmentSetup(env_path=str(env_file))
    config = setup.load()

    assert "DOCUMENT_MAPPER_TEST_RANDOM_DIR" not in config
    assert unrelated_dir.exists() is False


def test_resources_initialize_does_not_auto_create_images_directory(tmp_path):
    images_dir = tmp_path / "images-not-created"

    Resources.initialize(
        {
            "RESOURCES_BASE": "resources",
            "RESOURCES_IMAGES": str(images_dir),
        }
    )

    assert images_dir.exists() is False


def test_main_resolves_app_icon_from_resources_icons():
    icon_path = resolve_app_icon_path()

    assert icon_path is not None
    assert icon_path.name == "document-mapper.ico"
    assert icon_path.exists()


def test_qt_application_identity_uses_desktop_basename(monkeypatch):
    captured: dict[str, str] = {}

    class FakeCoreApplication:
        @staticmethod
        def setApplicationName(value):
            captured["app_name"] = value

        @staticmethod
        def setOrganizationName(value):
            captured["organization_name"] = value

        @staticmethod
        def setOrganizationDomain(value):
            captured["organization_domain"] = value

    class FakeGuiApplication:
        @staticmethod
        def setDesktopFileName(value):
            captured["desktop_file_name"] = value

    monkeypatch.setattr(app_icon_module, "QCoreApplication", FakeCoreApplication)
    monkeypatch.setattr(app_icon_module, "QGuiApplication", FakeGuiApplication)
    monkeypatch.setattr(
        app_icon_module,
        "detect_application_integration",
        lambda **_: ApplicationIntegrationTarget(
            platform="linux",
            desktop_file_name=DESKTOP_FILE_NAME,
            desktop_entry_filename=DESKTOP_ENTRY_FILENAME,
        ),
    )

    integration = configure_qt_application_identity(
        app_name="Document Mapper",
        organization_name="Younes Rabeh",
        organization_domain="github.com",
    )

    assert captured == {
        "app_name": "Document Mapper",
        "organization_name": "Younes Rabeh",
        "organization_domain": "github.com",
        "desktop_file_name": DESKTOP_FILE_NAME,
    }
    assert integration.platform == "linux"
    assert DESKTOP_FILE_NAME == "document-mapper"
    assert DESKTOP_ENTRY_FILENAME == "document-mapper.desktop"


def test_build_application_identifier_uses_domain_and_names():
    assert build_application_identifier(
        app_name="Document Mapper",
        organization_name="Younes Rabeh",
        organization_domain="github.com",
    ) == "com.github.younesrabeh.documentmapper"


def test_detect_application_integration_creates_windows_target(monkeypatch):
    monkeypatch.setattr(app_icon_module, "current_platform_family", lambda: "windows")

    integration = detect_application_integration(
        app_name="Document Mapper",
        organization_name="Younes Rabeh",
        organization_domain="github.com",
    )

    assert integration == ApplicationIntegrationTarget(
        platform="windows",
        windows_app_user_model_id="com.github.younesrabeh.documentmapper",
    )


def test_qt_application_identity_sets_windows_app_user_model_id(monkeypatch):
    captured: dict[str, str] = {}

    class FakeCoreApplication:
        @staticmethod
        def setApplicationName(value):
            captured["app_name"] = value

        @staticmethod
        def setOrganizationName(value):
            captured["organization_name"] = value

        @staticmethod
        def setOrganizationDomain(value):
            captured["organization_domain"] = value

    class FakeGuiApplication:
        @staticmethod
        def setDesktopFileName(_value):
            raise AssertionError("Desktop file name should not be set for Windows integration.")

    monkeypatch.setattr(app_icon_module, "QCoreApplication", FakeCoreApplication)
    monkeypatch.setattr(app_icon_module, "QGuiApplication", FakeGuiApplication)
    monkeypatch.setattr(
        app_icon_module,
        "detect_application_integration",
        lambda **_: ApplicationIntegrationTarget(
            platform="windows",
            windows_app_user_model_id="com.github.younesrabeh.documentmapper",
        ),
    )
    monkeypatch.setattr(
        app_icon_module,
        "_set_windows_app_user_model_id",
        lambda value: captured.setdefault("windows_app_user_model_id", value) == value,
    )

    integration = configure_qt_application_identity(
        app_name="Document Mapper",
        organization_name="Younes Rabeh",
        organization_domain="github.com",
    )

    assert captured == {
        "app_name": "Document Mapper",
        "organization_name": "Younes Rabeh",
        "organization_domain": "github.com",
        "windows_app_user_model_id": "com.github.younesrabeh.documentmapper",
    }
    assert integration.platform == "windows"

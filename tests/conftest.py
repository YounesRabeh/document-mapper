from __future__ import annotations

import os
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tests.helpers.fakes import (
    FakeExcelService,
    FakeGenerator,
    FakeLastSessionPersistenceService,
    FakeSessionStore,
)

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    """Provide a shared Qt application instance for GUI tests."""
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    """Return the root directory containing test fixtures."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def window_config() -> dict[str, object]:
    """Return base app/window configuration used by MainWindow tests."""
    return {
        "APP_NAME": "Document Mapper Test",
        "APP_ORGANIZATION": "Document Mapper Tests",
        "APP_LANGUAGE": "en",
        "WINDOW_WIDTH": 900,
        "WINDOW_HEIGHT": 600,
        "WINDOW_MIN_WIDTH": 800,
        "WINDOW_MIN_HEIGHT": 500,
        "WINDOW_TITLE": "Document Mapper",
        "WINDOW_THEME_MODE": "AUTO",
    }


@pytest.fixture
def clear_test_settings(window_config):
    """Clear persisted QSettings before and after each test using window config."""
    settings = QSettings(window_config["APP_ORGANIZATION"], window_config["APP_NAME"])
    settings.clear()
    yield
    settings.clear()


@pytest.fixture
def main_window_factory(qapp, window_config, clear_test_settings, tmp_path):
    """Create an isolated MainWindow factory with patched core dependencies."""
    from gui.windows import main_window as main_window_module

    resources: list[tuple[object, ExitStack]] = []
    state_dir = tmp_path / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    def _factory(
        *,
        fake_store: FakeSessionStore | None = None,
        excel_service: FakeExcelService | None = None,
        generator_factory=None,
    ):
        session_store = fake_store or FakeSessionStore()
        excel = excel_service or FakeExcelService()
        generator_side_effect = generator_factory or (lambda _excel: FakeGenerator())

        stack = ExitStack()
        stack.enter_context(patch.object(main_window_module, "ProjectSessionStore", return_value=session_store))
        stack.enter_context(patch.object(main_window_module, "ExcelDataService", return_value=excel))
        stack.enter_context(patch.object(main_window_module, "DocumentGenerator", side_effect=generator_side_effect))
        stack.enter_context(patch.object(main_window_module.ThemeManager, "_refresh_styled_widgets", return_value=None))
        stack.enter_context(patch.object(main_window_module.AppPaths, "state_dir", return_value=state_dir))
        stack.enter_context(
            patch.object(
                main_window_module,
                "LastSessionPersistenceService",
                side_effect=lambda store: FakeLastSessionPersistenceService(store),
            )
        )
        window = main_window_module.MainWindow(window_config)
        resources.append((window, stack))
        return window, session_store, main_window_module

    yield _factory

    for window, stack in reversed(resources):
        try:
            with patch.object(window, "_confirm_close_action", return_value="discard"):
                window.close()
        finally:
            stack.close()

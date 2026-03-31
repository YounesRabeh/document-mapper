from __future__ import annotations

import os
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from tests.helpers.fakes import FakeExcelService, FakeGenerator, FakeSessionStore

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    return app


@pytest.fixture(scope="session")
def fixture_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def window_config() -> dict[str, object]:
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
    settings = QSettings(window_config["APP_ORGANIZATION"], window_config["APP_NAME"])
    settings.clear()
    yield
    settings.clear()


@pytest.fixture
def main_window_factory(qapp, window_config, clear_test_settings):
    from gui import main_window as main_window_module

    resources: list[tuple[object, ExitStack]] = []

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
        stack.enter_context(patch.object(main_window_module, "CertificateGenerator", side_effect=generator_side_effect))
        window = main_window_module.MainWindow(window_config)
        resources.append((window, stack))
        return window, session_store, main_window_module

    yield _factory

    for window, stack in reversed(resources):
        try:
            window.close()
        finally:
            stack.close()

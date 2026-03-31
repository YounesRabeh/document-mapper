from __future__ import annotations

from types import SimpleNamespace

import pytest

from tests.helpers.gui import populate_setup_page


@pytest.fixture
def sample_project_files(tmp_path):
    workbook = tmp_path / "data.xlsx"
    template = tmp_path / "template.docx"
    workbook.write_text("placeholder", encoding="utf-8")
    template.write_text("Hello <<NOME>>", encoding="utf-8")
    return SimpleNamespace(root=tmp_path, workbook=workbook, template=template)


@pytest.fixture
def prepared_window(main_window_factory, sample_project_files):
    window, fake_store, main_window_module = main_window_factory()
    populate_setup_page(window, sample_project_files.workbook, sample_project_files.template, sample_project_files.root)
    return SimpleNamespace(
        window=window,
        fake_store=fake_store,
        main_window_module=main_window_module,
        files=sample_project_files,
    )

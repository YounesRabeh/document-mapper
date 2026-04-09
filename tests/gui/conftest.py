from __future__ import annotations

from types import SimpleNamespace
import zipfile

import pytest

from tests.helpers.gui import populate_setup_page


@pytest.fixture
def sample_project_files(tmp_path):
    """Create temporary workbook/template files used by GUI workflow tests."""
    workbook = tmp_path / "data.xlsx"
    template = tmp_path / "template.docx"
    workbook.write_text("placeholder", encoding="utf-8")
    with zipfile.ZipFile(template, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Hello &lt;NAME&gt;</w:t></w:r></w:p></w:body></w:document>"
            ),
        )
    return SimpleNamespace(root=tmp_path, workbook=workbook, template=template)


@pytest.fixture
def prepared_window(main_window_factory, sample_project_files):
    """Return a window pre-populated with setup data and helper handles."""
    window, fake_store, main_window_module = main_window_factory()
    populate_setup_page(window, sample_project_files.workbook, sample_project_files.template, sample_project_files.root)
    return SimpleNamespace(
        window=window,
        fake_store=fake_store,
        main_window_module=main_window_module,
        files=sample_project_files,
    )

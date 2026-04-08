# Tests

This project uses `pytest` for the full test suite.

## Setup

Install dependencies from the project root:

```bash
python -m pip install -r requirements.txt
```

## Run the suite

Run everything:

```bash
python -m pytest
```

Run with compact output:

```bash
python -m pytest -q
```

For headless environments, CI, or Linux shells without a working display session:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest -q
```

## Run specific areas

Service tests:

```bash
python -m pytest tests/core -q
```

GUI tests:

```bash
python -m pytest tests/gui -q
```

Single file:

```bash
python -m pytest tests/gui/workflow/test_mapping_page.py -q
```

Single test:

```bash
python -m pytest tests/gui/workflow/test_mapping_page.py -k delimiter -q
```

## Structure

- `tests/core/mapping/`: Excel, generator, session, template, and model tests
- `tests/core/project/`: project document and template-catalog tests
- `tests/core/util/`: app-path and resource resolution tests
- `tests/core/manager/`: localization catalog and manager-level tests
- `tests/gui/windows/`: main window flow and project save/open behavior
- `tests/gui/workflow/`: mapping page and workflow-specific logic
- `tests/gui/dialogs/`: dialog behavior
- `tests/gui/controllers/`: controller-only GUI state logic
- `tests/helpers/`: shared fakes and GUI helpers
- `tests/fixtures/`: sample `.xlsx` and `.docx` inputs used by tests
- `tests/conftest.py`: shared pytest fixtures for the whole suite
- `tests/gui/conftest.py`: GUI-specific fixtures

## Notes

- The suite is fully `pytest`-based; the old `unittest` layout has been removed.
- GUI tests use PySide6 and may require `QT_QPA_PLATFORM=offscreen` outside a normal desktop session.
- The fixture workbook and template under `tests/fixtures/` are safe to edit when you intentionally want to refresh sample test data.
- Run tests from the project root so relative paths and fixture discovery stay consistent.

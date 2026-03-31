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
python -m pytest tests/services -q
```

GUI tests:

```bash
python -m pytest tests/gui -q
```

Single file:

```bash
python -m pytest tests/gui/test_mapping_page.py -q
```

Single test:

```bash
python -m pytest tests/gui/test_mapping_page.py -k delimiter -q
```

## Structure

- `tests/services/`: service, generator, session, and path logic
- `tests/gui/`: workflow navigation and window behavior
- `tests/helpers/`: shared fakes and GUI helpers
- `tests/fixtures/`: sample `.xlsx` and `.docx` inputs used by tests
- `tests/conftest.py`: shared pytest fixtures for the whole suite
- `tests/gui/conftest.py`: GUI-specific fixtures

## Notes

- The suite is fully `pytest`-based; the old `unittest` layout has been removed.
- GUI tests use PySide6 and may require `QT_QPA_PLATFORM=offscreen` outside a normal desktop session.
- The fixture workbook and template under `tests/fixtures/` are safe to edit when you intentionally want to refresh sample test data.
- Run tests from the project root so relative paths and fixture discovery stay consistent.

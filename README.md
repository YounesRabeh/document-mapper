# Document Mapper

PySide6 desktop app for generating certificate `.docx` files from Excel data with explicit placeholder mapping and optional PDF export via LibreOffice.

## Testing

Run the full suite with:

```bash
QT_QPA_PLATFORM=offscreen pytest -q
```

The tests are split by feature under `tests/services/` and `tests/gui/`, with shared fixtures in `tests/conftest.py` and reusable fakes in `tests/helpers/`.

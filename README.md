# Document Mapper

PySide6 desktop app for generating certificate `.docx` files from Excel data with explicit placeholder mapping and optional PDF export via LibreOffice.

## Testing

Test documentation lives in [tests/README.md](/home/yuyu/Desktop/DEV/Python%20Projects/document-mapper/tests/README.md).

Quick start:

```bash
python -m pip install -r requirements.txt
python -m pytest
```

For GUI/headless environments, see the dedicated test guide for the `offscreen` command and the split between `tests/services/` and `tests/gui/`.

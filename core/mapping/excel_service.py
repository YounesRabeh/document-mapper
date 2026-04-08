from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from core.mapping.models import ExcelPreview, MappingEntry


def normalize_column_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).upper()


class ExcelDataService:
    def __init__(self):
        self._preview_cache: dict[str, tuple[tuple[int, int], ExcelPreview]] = {}

    def inspect(self, excel_path: str) -> ExcelPreview:
        path = self._resolve_path(excel_path)
        cache_key = str(path)
        signature = self._build_signature(path)
        cached = self._preview_cache.get(cache_key)
        if cached and cached[0] == signature:
            preview = cached[1]
            return ExcelPreview(columns=list(preview.columns), row_count=preview.row_count)

        dataframe = self.read_dataframe(str(path))
        preview = ExcelPreview(
            columns=[str(column) for column in dataframe.columns],
            row_count=len(dataframe.index),
        )
        self._preview_cache[cache_key] = (signature, preview)
        return ExcelPreview(columns=list(preview.columns), row_count=preview.row_count)

    def read_dataframe(self, excel_path: str) -> pd.DataFrame:
        path = self._resolve_path(excel_path)
        return pd.read_excel(path, header=0)

    def clear_cache(self, excel_path: str | None = None):
        if excel_path:
            try:
                cache_key = str(Path(excel_path).expanduser().resolve())
            except OSError:
                return
            self._preview_cache.pop(cache_key, None)
            return
        self._preview_cache.clear()

    def build_column_lookup(self, columns: list[str]) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for column in columns:
            normalized = normalize_column_name(column)
            if normalized and normalized not in lookup:
                lookup[normalized] = column
        return lookup

    def validate_mappings(self, columns: list[str], mappings: list[MappingEntry]) -> list[str]:
        errors: list[str] = []
        lookup = self.build_column_lookup(columns)

        placeholders: set[str] = set()
        for index, mapping in enumerate(mappings, start=1):
            placeholder = mapping.placeholder.strip()
            if not placeholder:
                errors.append(f"Mapping row {index} is missing a placeholder.")
            elif placeholder in placeholders:
                errors.append(f"Placeholder '{placeholder}' is mapped more than once.")
            placeholders.add(placeholder)

            column_name = mapping.column_name.strip()
            if not column_name:
                errors.append(f"Mapping row {index} is missing an Excel column.")
                continue
            if normalize_column_name(column_name) not in lookup:
                errors.append(f"Excel column '{column_name}' is not available in the selected workbook.")

        return errors

    def _resolve_path(self, excel_path: str) -> Path:
        if not excel_path:
            raise ValueError("Excel path is empty.")
        path = Path(excel_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
        return path

    def _build_signature(self, path: Path) -> tuple[int, int]:
        stat = path.stat()
        return stat.st_mtime_ns, stat.st_size

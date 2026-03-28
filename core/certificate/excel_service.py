from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from core.certificate.models import ExcelPreview, MappingEntry


def normalize_column_name(value: str) -> str:
    return re.sub(r"\s+", " ", str(value).strip()).upper()


class ExcelDataService:
    def inspect(self, excel_path: str) -> ExcelPreview:
        dataframe = self.read_dataframe(excel_path)
        return ExcelPreview(
            columns=[str(column) for column in dataframe.columns],
            row_count=len(dataframe.index),
        )

    def read_dataframe(self, excel_path: str) -> pd.DataFrame:
        if not excel_path:
            raise ValueError("Excel path is empty.")
        path = Path(excel_path)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {excel_path}")
        return pd.read_excel(path, header=0)

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

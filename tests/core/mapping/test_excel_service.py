from __future__ import annotations

import pandas as pd

from core.mapping.excel_service import ExcelDataService, normalize_column_name
from core.mapping.models import MappingEntry


def test_normalize_column_name():
    assert normalize_column_name("  nome   completo ") == "NOME COMPLETO"


def test_validate_mappings_uses_normalized_columns():
    service = ExcelDataService()

    errors = service.validate_mappings(
        [" Nome ", "COGNOME"],
        [MappingEntry(placeholder="<<NOME>>", column_name="nome")],
    )

    assert errors == []


def test_inspect_uses_cache_until_cleared(tmp_path):
    class CountingExcelService(ExcelDataService):
        def __init__(self):
            super().__init__()
            self.read_calls = 0

        def read_dataframe(self, _excel_path: str) -> pd.DataFrame:
            self.read_calls += 1
            return pd.DataFrame([{"NOME": "Ada"}])

    service = CountingExcelService()
    excel_path = tmp_path / "data.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")

    preview_one = service.inspect(str(excel_path))
    preview_two = service.inspect(str(excel_path))
    service.clear_cache(str(excel_path))
    preview_three = service.inspect(str(excel_path))

    assert preview_one.columns == ["NOME"]
    assert preview_two.columns == ["NOME"]
    assert preview_three.columns == ["NOME"]
    assert service.read_calls == 2

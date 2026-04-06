from __future__ import annotations

from types import SimpleNamespace

from core.certificate.models import MappingEntry
from gui.workflow.mapping_logic import MappingContextService


class _ExcelStub:
    def inspect(self, _path: str):
        return SimpleNamespace(columns=["NAME", "LASTNAME"], row_count=5)


class _TemplateStub:
    def extract_placeholders(self, _path: str, delimiter: str):
        return [f"{delimiter}NAME>", f"{delimiter}LASTNAME>"]


def test_mapping_context_loads_workbook_columns_and_tokens():
    context = MappingContextService(_ExcelStub(), _TemplateStub())

    result = context.load_workbook_columns("/tmp/workbook.xlsx")

    assert result.columns == ["NAME", "LASTNAME"]
    assert result.row_count == 5
    assert context.output_naming_tokens(result.columns) == ["NAME", "LASTNAME", "ROW", "TEMPLATE"]


def test_mapping_context_prunes_stale_detected_mappings_only():
    context = MappingContextService(_ExcelStub(), _TemplateStub())
    mappings = [
        MappingEntry(placeholder="<NAME>", column_name="NAME"),
        MappingEntry(placeholder="<LASTNAME>", column_name="LASTNAME"),
        MappingEntry(placeholder="<CUSTOM>", column_name="NOTE"),
    ]

    pruned = context.prune_stale_detected_mappings(
        mappings,
        previous_detected_placeholders={"<NAME>", "<LASTNAME>"},
        current_detected_placeholders=["<NAME>"],
    )

    assert [entry.placeholder for entry in pruned] == ["<NAME>", "<CUSTOM>"]


def test_mapping_context_builds_rows_from_detected_and_manual_mappings():
    context = MappingContextService(_ExcelStub(), _TemplateStub())
    merged, persisted = context.build_mapping_rows(
        ["<NAME>", "<LASTNAME>"],
        [
            MappingEntry(placeholder="<NAME>", column_name="NAME"),
            MappingEntry(placeholder="<CUSTOM>", column_name="NOTE"),
        ],
    )

    assert [entry.placeholder for entry in merged] == ["<NAME>", "<LASTNAME>", "<CUSTOM>"]
    assert merged[0].column_name == "NAME"
    assert merged[1].column_name == ""
    assert merged[2].column_name == "NOTE"
    assert [entry.placeholder for entry in persisted] == ["<NAME>", "<LASTNAME>", "<CUSTOM>"]

from __future__ import annotations

from dataclasses import dataclass, field

from core.certificate.models import MappingEntry


@dataclass(slots=True)
class WorkbookColumnsResult:
    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    error: Exception | None = None


@dataclass(slots=True)
class PlaceholderDetectionResult:
    placeholders: list[str] = field(default_factory=list)
    error: Exception | None = None


class MappingContextService:
    def __init__(self, excel_service, template_service):
        self.excel_service = excel_service
        self.template_service = template_service

    def load_workbook_columns(self, excel_path: str) -> WorkbookColumnsResult:
        if not excel_path:
            return WorkbookColumnsResult()
        try:
            preview = self.excel_service.inspect(excel_path)
        except Exception as exc:  # noqa: BLE001
            return WorkbookColumnsResult(error=exc)
        return WorkbookColumnsResult(columns=list(preview.columns), row_count=preview.row_count)

    def detect_placeholders(self, template_path: str, delimiter: str) -> PlaceholderDetectionResult:
        if not template_path or not delimiter:
            return PlaceholderDetectionResult()
        try:
            placeholders = self.template_service.extract_placeholders(template_path, delimiter)
        except Exception as exc:  # noqa: BLE001
            return PlaceholderDetectionResult(error=exc)
        return PlaceholderDetectionResult(placeholders=list(placeholders))

    @staticmethod
    def output_naming_tokens(columns: list[str]) -> list[str]:
        tokens = list(columns)
        tokens.extend(["ROW", "TEMPLATE"])
        return tokens

    @staticmethod
    def prune_stale_detected_mappings(
        mappings: list[MappingEntry],
        previous_detected_placeholders: set[str],
        current_detected_placeholders: list[str],
    ) -> list[MappingEntry]:
        if not previous_detected_placeholders:
            return [MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name) for entry in mappings]

        stale_placeholders = previous_detected_placeholders.difference(current_detected_placeholders)
        if not stale_placeholders:
            return [MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name) for entry in mappings]

        return [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in mappings
            if entry.placeholder.strip() not in stale_placeholders
        ]

    @staticmethod
    def build_mapping_rows(
        detected_placeholders: list[str],
        current_mappings: list[MappingEntry],
    ) -> tuple[list[MappingEntry], list[MappingEntry]]:
        merged_mappings: list[MappingEntry] = []
        detected_lookup = {placeholder: None for placeholder in detected_placeholders}
        manual_mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in current_mappings
        ]

        for placeholder in detected_placeholders:
            matching = next((entry for entry in manual_mappings if entry.placeholder == placeholder), None)
            if matching is not None:
                merged_mappings.append(matching)
            else:
                merged_mappings.append(MappingEntry(placeholder=placeholder))

        for entry in manual_mappings:
            placeholder = entry.placeholder.strip()
            if not placeholder or placeholder not in detected_lookup:
                merged_mappings.append(entry)

        if not merged_mappings:
            return [MappingEntry()], []

        persisted_mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in merged_mappings
            if entry.placeholder or entry.column_name
        ]
        return merged_mappings, persisted_mappings

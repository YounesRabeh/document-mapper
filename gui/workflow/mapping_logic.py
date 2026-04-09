from __future__ import annotations

from dataclasses import dataclass, field

from core.mapping.models import MappingEntry


@dataclass(slots=True)
class WorkbookColumnsResult:
    """Workbook-column loading result with optional error payload."""

    columns: list[str] = field(default_factory=list)
    row_count: int = 0
    error: Exception | None = None


@dataclass(slots=True)
class PlaceholderDetectionResult:
    """Template placeholder detection result with optional error payload."""

    placeholders: list[str] = field(default_factory=list)
    error: Exception | None = None


class MappingContextService:
    """Facade used by MappingPage to load columns/placeholders and merge mappings."""

    def __init__(self, excel_service, template_service):
        self.excel_service = excel_service
        self.template_service = template_service

    def load_workbook_columns(self, excel_path: str) -> WorkbookColumnsResult:
        """Inspect workbook and return available columns/row count."""
        if not excel_path:
            return WorkbookColumnsResult()
        try:
            preview = self.excel_service.inspect(excel_path)
        except Exception as exc:  # noqa: BLE001
            return WorkbookColumnsResult(error=exc)
        return WorkbookColumnsResult(columns=list(preview.columns), row_count=preview.row_count)

    def detect_placeholders(self, template_path: str, delimiter: str) -> PlaceholderDetectionResult:
        """Extract placeholders from template for the provided delimiter."""
        if not template_path or not delimiter:
            return PlaceholderDetectionResult()
        try:
            placeholders = self.template_service.extract_placeholders(template_path, delimiter)
        except Exception as exc:  # noqa: BLE001
            return PlaceholderDetectionResult(error=exc)
        return PlaceholderDetectionResult(placeholders=list(placeholders))

    @staticmethod
    def output_naming_tokens(columns: list[str]) -> list[str]:
        """Return output naming token suggestions from workbook columns plus built-ins."""
        tokens = list(columns)
        tokens.extend(["ROW", "TEMPLATE"])
        return tokens

    @staticmethod
    def prune_stale_detected_mappings(
        mappings: list[MappingEntry],
        previous_detected_placeholders: set[str],
        current_detected_placeholders: list[str],
    ) -> list[MappingEntry]:
        """Remove mappings tied only to placeholders no longer detected."""
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
        """Merge detected placeholders with manual rows and return UI+persisted rows."""
        manual_mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in current_mappings
        ]

        mapped_by_placeholder: dict[str, MappingEntry] = {}
        for entry in manual_mappings:
            placeholder = entry.placeholder.strip()
            if placeholder and placeholder not in mapped_by_placeholder:
                mapped_by_placeholder[placeholder] = entry

        merged_mappings: list[MappingEntry] = []
        detected_seen: set[str] = set()
        for placeholder in detected_placeholders:
            normalized_placeholder = placeholder.strip()
            if not normalized_placeholder or normalized_placeholder in detected_seen:
                continue
            detected_seen.add(normalized_placeholder)
            existing = mapped_by_placeholder.get(normalized_placeholder)
            merged_mappings.append(
                MappingEntry(
                    placeholder=normalized_placeholder,
                    column_name=existing.column_name if existing is not None else "",
                )
            )

        for entry in manual_mappings:
            placeholder = entry.placeholder.strip()
            if placeholder and placeholder in detected_seen:
                continue
            merged_mappings.append(MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name))

        persisted_mappings = [
            MappingEntry(placeholder=entry.placeholder, column_name=entry.column_name)
            for entry in merged_mappings
            if entry.placeholder or entry.column_name
        ]
        return merged_mappings, persisted_mappings

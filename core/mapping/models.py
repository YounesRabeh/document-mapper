from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any
from uuid import uuid4

from core.enums.app_themes import AppTheme

DEFAULT_IMPORTED_TEMPLATE_TYPE = "Default template"
DEFAULT_IMPORTED_TEMPLATE_NAME = "Default template 01"
DEFAULT_PLACEHOLDER_DELIMITER = "<"
DEFAULT_OUTPUT_NAMING_SCHEMA = "{NAME}_{LASTNAME}_{TEMPLATE}"
DELIMITER_CLOSING_MAP = {
    "<": ">",
    "{": "}",
    "[": "]",
    "(": ")",
}


def normalize_template_name(value: str) -> str:
    normalized = re.sub(r"\.(docx?)$", "", str(value).strip(), flags=re.IGNORECASE)
    return normalized.strip()


def normalize_template_type_name(value: str) -> str:
    normalized = re.sub(r"\s+", " ", str(value or "").strip())
    if normalized.casefold() == "imported":
        return DEFAULT_IMPORTED_TEMPLATE_TYPE
    return normalized


def normalize_placeholder_delimiter(value: str) -> str:
    return str(value or "").strip()


def normalize_output_naming_schema(value: str) -> str:
    return str(value or "").strip()


def normalize_theme_mode(value: Any) -> str:
    if isinstance(value, AppTheme):
        return value.name
    candidate = str(value or "").strip().upper()
    return candidate if candidate in AppTheme.__members__ else ""


def derive_placeholder_boundaries(delimiter: str) -> tuple[str, str]:
    normalized = normalize_placeholder_delimiter(delimiter) or DEFAULT_PLACEHOLDER_DELIMITER
    closing = "".join(DELIMITER_CLOSING_MAP.get(char, char) for char in normalized)
    return normalized, closing


def infer_placeholder_delimiter_from_mappings(mappings: list["MappingEntry"]) -> str:
    for mapping in mappings:
        placeholder = mapping.placeholder.strip()
        if not placeholder or len(placeholder) < 3:
            continue
        max_prefix = len(placeholder) // 2
        for prefix_length in range(max_prefix, 0, -1):
            candidate = placeholder[:prefix_length]
            start, end = derive_placeholder_boundaries(candidate)
            if not placeholder.endswith(end):
                continue
            inner_text = placeholder[len(start) : len(placeholder) - len(end)]
            if inner_text:
                return start
        break
    return DEFAULT_PLACEHOLDER_DELIMITER


def generate_template_entry_id() -> str:
    return uuid4().hex


@dataclass(slots=True)
class MappingEntry:
    placeholder: str = ""
    column_name: str = ""

    def to_dict(self) -> dict[str, str]:
        return {
            "placeholder": self.placeholder,
            "column_name": self.column_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "MappingEntry":
        payload = data or {}
        return cls(
            placeholder=str(payload.get("placeholder", "")).strip(),
            column_name=str(payload.get("column_name", "")).strip(),
        )


@dataclass(slots=True)
class ProjectTemplateType:
    name: str = ""

    def __post_init__(self):
        self.name = normalize_template_type_name(self.name)

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProjectTemplateType":
        payload = data or {}
        return cls(name=str(payload.get("name", "")).strip())


@dataclass(slots=True)
class ProjectTemplateEntry:
    id: str = field(default_factory=generate_template_entry_id)
    display_name: str = ""
    type_name: str = ""
    relative_path: str = ""
    source_path: str = ""
    is_managed: bool = False

    def __post_init__(self):
        self.id = str(self.id or generate_template_entry_id()).strip() or generate_template_entry_id()
        self.display_name = normalize_template_name(self.display_name)
        self.type_name = normalize_template_type_name(self.type_name)
        self.relative_path = str(self.relative_path or "").strip()
        self.source_path = str(self.source_path or "").strip()
        self.is_managed = bool(self.is_managed)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "type_name": self.type_name,
            "relative_path": self.relative_path,
            "source_path": self.source_path,
            "is_managed": self.is_managed,
        }

    def to_project_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "type_name": self.type_name,
            "relative_path": self.relative_path,
            "is_managed": self.is_managed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProjectTemplateEntry":
        payload = data or {}
        return cls(
            id=str(payload.get("id", "")).strip() or generate_template_entry_id(),
            display_name=str(payload.get("display_name", "")).strip(),
            type_name=str(payload.get("type_name", "")).strip(),
            relative_path=str(payload.get("relative_path", "")).strip(),
            source_path=str(payload.get("source_path", "")).strip(),
            is_managed=bool(payload.get("is_managed", False)),
        )

    @classmethod
    def from_project_dict(cls, data: dict[str, Any] | None) -> "ProjectTemplateEntry":
        entry = cls.from_dict(data)
        if entry.is_managed and entry.relative_path:
            entry.source_path = ""
        return entry

    @property
    def label(self) -> str:
        if self.display_name:
            return self.display_name
        if self.relative_path:
            return normalize_template_name(Path(self.relative_path).name)
        if self.source_path:
            return normalize_template_name(Path(self.source_path).name)
        return "Template"


@dataclass(slots=True)
class ProjectSession:
    excel_path: str = ""
    template_path: str = ""
    template_override_path: str = ""
    output_dir: str = ""
    license_path: str = ""
    theme_mode: str = ""
    selected_template_type: str = ""
    selected_template: str = ""
    template_types: list[ProjectTemplateType] = field(default_factory=list)
    templates: list[ProjectTemplateEntry] = field(default_factory=list)
    output_naming_schema: str = DEFAULT_OUTPUT_NAMING_SCHEMA
    placeholder_delimiter: str = DEFAULT_PLACEHOLDER_DELIMITER
    detected_placeholder_delimiter: str = ""
    detected_placeholder_count: int = 0
    export_pdf: bool = False
    pdf_timeout_seconds: int = 300
    mappings: list[MappingEntry] = field(default_factory=list)

    def __post_init__(self):
        self.template_path = str(self.template_path or "").strip()
        self.template_override_path = str(self.template_override_path or "").strip()
        self.output_dir = str(self.output_dir or "").strip()
        self.license_path = str(self.license_path or "").strip()
        self.theme_mode = normalize_theme_mode(self.theme_mode)
        self.selected_template_type = normalize_template_type_name(self.selected_template_type)
        self.selected_template = str(self.selected_template or "").strip()
        self.template_types = [entry for entry in self._normalize_template_types(self.template_types) if entry.name]
        self.templates = [entry for entry in self._normalize_templates(self.templates) if entry.type_name]

        delimiter = normalize_placeholder_delimiter(self.placeholder_delimiter)
        if not delimiter:
            delimiter = infer_placeholder_delimiter_from_mappings(self.mappings)
        self.placeholder_delimiter = delimiter
        self.output_naming_schema = normalize_output_naming_schema(self.output_naming_schema)
        self.detected_placeholder_delimiter = normalize_placeholder_delimiter(self.detected_placeholder_delimiter)
        try:
            self.detected_placeholder_count = max(0, int(self.detected_placeholder_count))
        except (TypeError, ValueError):
            self.detected_placeholder_count = 0
        self._ensure_template_catalog_consistency()

    @property
    def placeholder_start(self) -> str:
        return derive_placeholder_boundaries(self.placeholder_delimiter)[0]

    @property
    def placeholder_end(self) -> str:
        return derive_placeholder_boundaries(self.placeholder_delimiter)[1]

    @property
    def active_template_name(self) -> str:
        if self.template_override_path:
            return normalize_template_name(Path(self.template_override_path).name)
        template_entry = self.selected_template_entry()
        if template_entry is not None:
            return template_entry.label
        if self.template_path:
            return normalize_template_name(Path(self.template_path).name)
        return ""

    def selected_template_entry(self) -> ProjectTemplateEntry | None:
        if not self.selected_template:
            return None
        return next((entry for entry in self.templates if entry.id == self.selected_template), None)

    def templates_for_selected_type(self) -> list[ProjectTemplateEntry]:
        if not self.selected_template_type:
            return []
        return [entry for entry in self.templates if entry.type_name == self.selected_template_type]

    def templates_for_type(self, type_name: str) -> list[ProjectTemplateEntry]:
        normalized = normalize_template_type_name(type_name)
        return [entry for entry in self.templates if entry.type_name == normalized]

    def to_dict(self) -> dict[str, Any]:
        return self._to_payload(project_mode=False)

    def to_project_dict(self) -> dict[str, Any]:
        return self._to_payload(project_mode=True)

    def _to_payload(self, *, project_mode: bool) -> dict[str, Any]:
        return {
            "excel_path": self.excel_path,
            "template_path": self.template_path,
            "template_override_path": self.template_override_path,
            "output_dir": self.output_dir,
            "license_path": self.license_path,
            "theme_mode": self.theme_mode,
            "selected_template_type": self.selected_template_type,
            "selected_template": self.selected_template,
            "template_types": [entry.to_dict() for entry in self.template_types],
            "templates": [
                entry.to_project_dict() if project_mode else entry.to_dict()
                for entry in self.templates
            ],
            "output_naming_schema": self.output_naming_schema,
            "placeholder_delimiter": self.placeholder_delimiter,
            "detected_placeholder_delimiter": self.detected_placeholder_delimiter,
            "detected_placeholder_count": self.detected_placeholder_count,
            "export_pdf": self.export_pdf,
            "pdf_timeout_seconds": self.pdf_timeout_seconds,
            "mappings": [entry.to_dict() for entry in self.mappings],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProjectSession":
        return cls._from_payload(data, project_mode=False)

    def clone(self) -> "ProjectSession":
        return ProjectSession.from_dict(self.to_dict())

    @classmethod
    def from_project_dict(cls, data: dict[str, Any] | None) -> "ProjectSession":
        return cls._from_payload(data, project_mode=True)

    @classmethod
    def _from_payload(cls, data: dict[str, Any] | None, *, project_mode: bool) -> "ProjectSession":
        payload = data or {}
        raw_timeout = payload.get("pdf_timeout_seconds", 300)
        try:
            timeout = int(raw_timeout)
        except (TypeError, ValueError):
            timeout = 300

        raw_delimiter = str(payload.get("placeholder_delimiter", "")).strip()
        raw_output_naming_schema = (
            normalize_output_naming_schema(payload.get("output_naming_schema", ""))
            if "output_naming_schema" in payload
            else DEFAULT_OUTPUT_NAMING_SCHEMA
        )
        if not raw_delimiter:
            legacy_start = str(payload.get("placeholder_start", "")).strip()
            legacy_end = str(payload.get("placeholder_end", "")).strip()
            if legacy_start and legacy_end:
                if legacy_end == derive_placeholder_boundaries(legacy_start)[1]:
                    raw_delimiter = legacy_start
                elif legacy_start == legacy_end:
                    raw_delimiter = legacy_start

        session = cls(
            excel_path=str(payload.get("excel_path", "")).strip(),
            template_path=str(payload.get("template_path", "")).strip(),
            template_override_path=str(payload.get("template_override_path", "")).strip(),
            output_dir=str(payload.get("output_dir", "")).strip(),
            license_path=str(payload.get("license_path", "")).strip(),
            theme_mode=payload.get("theme_mode", ""),
            selected_template_type=str(payload.get("selected_template_type", "")).strip(),
            selected_template=str(payload.get("selected_template", "")).strip(),
            template_types=[
                ProjectTemplateType.from_dict(entry)
                for entry in payload.get("template_types", [])
                if isinstance(entry, dict)
            ],
            templates=[
                (
                    ProjectTemplateEntry.from_project_dict(entry)
                    if project_mode
                    else ProjectTemplateEntry.from_dict(entry)
                )
                for entry in payload.get("templates", [])
                if isinstance(entry, dict)
            ],
            output_naming_schema=raw_output_naming_schema,
            placeholder_delimiter=raw_delimiter,
            detected_placeholder_delimiter=str(payload.get("detected_placeholder_delimiter", "")).strip(),
            detected_placeholder_count=payload.get("detected_placeholder_count", 0),
            export_pdf=bool(payload.get("export_pdf", False)),
            pdf_timeout_seconds=max(1, timeout),
            mappings=[
                MappingEntry.from_dict(entry)
                for entry in payload.get("mappings", [])
                if isinstance(entry, dict)
            ],
        )
        session._migrate_legacy_template_fields(payload)
        session._ensure_template_catalog_consistency()
        return session

    def _migrate_legacy_template_fields(self, payload: dict[str, Any]):
        if self.template_types or self.templates:
            return

        legacy_template_path = str(payload.get("template_path", "")).strip()
        if not legacy_template_path:
            return

        imported_type = ProjectTemplateType(DEFAULT_IMPORTED_TEMPLATE_TYPE)
        imported_entry = ProjectTemplateEntry(
            display_name=DEFAULT_IMPORTED_TEMPLATE_NAME,
            type_name=imported_type.name,
            source_path=legacy_template_path,
            is_managed=False,
        )
        self.template_types = [imported_type]
        self.templates = [imported_entry]
        self.selected_template_type = imported_type.name
        self.selected_template = imported_entry.id
        if not self.template_path:
            self.template_path = legacy_template_path

    def _normalize_template_types(self, entries: list[ProjectTemplateType | dict[str, Any] | str]) -> list[ProjectTemplateType]:
        normalized: list[ProjectTemplateType] = []
        seen: set[str] = set()
        for entry in entries:
            template_type = entry if isinstance(entry, ProjectTemplateType) else (
                ProjectTemplateType.from_dict(entry) if isinstance(entry, dict) else ProjectTemplateType(str(entry))
            )
            if not template_type.name:
                continue
            key = template_type.name.casefold()
            if key in seen:
                continue
            normalized.append(template_type)
            seen.add(key)
        return normalized

    def _normalize_templates(
        self,
        entries: list[ProjectTemplateEntry | dict[str, Any]],
    ) -> list[ProjectTemplateEntry]:
        normalized: list[ProjectTemplateEntry] = []
        seen: set[str] = set()
        for entry in entries:
            template_entry = entry if isinstance(entry, ProjectTemplateEntry) else ProjectTemplateEntry.from_dict(entry)
            if not template_entry.type_name:
                continue
            key = template_entry.id.casefold()
            if key in seen:
                continue
            if not template_entry.display_name:
                template_entry.display_name = template_entry.label
            normalized.append(template_entry)
            seen.add(key)
        return normalized

    def _ensure_template_catalog_consistency(self):
        type_names = {entry.name for entry in self.template_types}
        for entry in self.templates:
            if entry.type_name and entry.type_name not in type_names:
                self.template_types.append(ProjectTemplateType(entry.type_name))
                type_names.add(entry.type_name)

        if self.selected_template:
            selected_entry = self.selected_template_entry()
            if selected_entry is None:
                self.selected_template = ""
            elif not self.selected_template_type:
                self.selected_template_type = selected_entry.type_name

        if self.selected_template_type and self.selected_template_type not in {entry.name for entry in self.template_types}:
            self.selected_template_type = ""

        if not self.selected_template_type and self.template_types:
            self.selected_template_type = self.template_types[0].name

        if not self.selected_template and self.selected_template_type:
            entries = self.templates_for_selected_type()
            if entries:
                self.selected_template = entries[0].id


@dataclass(slots=True)
class GenerationResult:
    total_rows: int = 0
    success_count: int = 0
    generated_docx_paths: list[str] = field(default_factory=list)
    generated_pdf_paths: list[str] = field(default_factory=list)
    log_path: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExcelPreview:
    columns: list[str] = field(default_factory=list)
    row_count: int = 0

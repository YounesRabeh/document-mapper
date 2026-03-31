from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any

CERTIFICATE_TYPE_OPTIONS = (
    "MODELLO ATTESTATO integrale PS 12 ORE tipo B e C",
    "MODELLO ATTESTATO integrale PS 16 ORE tipo A",
    "MODELLO ATTESTATO RETRAINING PS 4h tipo B,C",
    "MODELLO ATTESTATO RETRAINING PS 6h tipo A",
)
DEFAULT_CERTIFICATE_TYPE = CERTIFICATE_TYPE_OPTIONS[0]
DEFAULT_PLACEHOLDER_DELIMITER = "<<"
DEFAULT_OUTPUT_NAMING_SCHEMA = "{NOME}_{COGNOME}_attestato_{CERTIFICATE_TYPE}"
DELIMITER_CLOSING_MAP = {
    "<": ">",
    "{": "}",
    "[": "]",
    "(": ")",
}


def normalize_certificate_type(value: str) -> str:
    normalized = re.sub(r"\.(docx?)$", "", str(value).strip(), flags=re.IGNORECASE)
    if not normalized:
        return DEFAULT_CERTIFICATE_TYPE

    canonical_options = {option.casefold(): option for option in CERTIFICATE_TYPE_OPTIONS}
    return canonical_options.get(normalized.casefold(), normalized)


def normalize_placeholder_delimiter(value: str) -> str:
    return str(value or "").strip()


def normalize_output_naming_schema(value: str) -> str:
    return str(value or "").strip()


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
class ProjectSession:
    excel_path: str = ""
    template_path: str = ""
    output_dir: str = ""
    license_path: str = ""
    certificate_type: str = DEFAULT_CERTIFICATE_TYPE
    placeholder_delimiter: str = DEFAULT_PLACEHOLDER_DELIMITER
    output_naming_schema: str = DEFAULT_OUTPUT_NAMING_SCHEMA
    detected_placeholder_delimiter: str = ""
    detected_placeholder_count: int = 0
    export_pdf: bool = False
    pdf_timeout_seconds: int = 300
    mappings: list[MappingEntry] = field(default_factory=list)

    def __post_init__(self):
        self.certificate_type = normalize_certificate_type(self.certificate_type)
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

    @property
    def placeholder_start(self) -> str:
        return derive_placeholder_boundaries(self.placeholder_delimiter)[0]

    @property
    def placeholder_end(self) -> str:
        return derive_placeholder_boundaries(self.placeholder_delimiter)[1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "excel_path": self.excel_path,
            "template_path": self.template_path,
            "output_dir": self.output_dir,
            "license_path": self.license_path,
            "certificate_type": self.certificate_type,
            "placeholder_delimiter": self.placeholder_delimiter,
            "output_naming_schema": self.output_naming_schema,
            "detected_placeholder_delimiter": self.detected_placeholder_delimiter,
            "detected_placeholder_count": self.detected_placeholder_count,
            "export_pdf": self.export_pdf,
            "pdf_timeout_seconds": self.pdf_timeout_seconds,
            "mappings": [entry.to_dict() for entry in self.mappings],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "ProjectSession":
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

        return cls(
            excel_path=str(payload.get("excel_path", "")).strip(),
            template_path=str(payload.get("template_path", "")).strip(),
            output_dir=str(payload.get("output_dir", "")).strip(),
            license_path=str(payload.get("license_path", "")).strip(),
            certificate_type=normalize_certificate_type(payload.get("certificate_type", DEFAULT_CERTIFICATE_TYPE)),
            placeholder_delimiter=raw_delimiter,
            output_naming_schema=raw_output_naming_schema,
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

    def clone(self) -> "ProjectSession":
        return ProjectSession.from_dict(self.to_dict())


@dataclass(slots=True)
class GenerationResult:
    total_rows: int = 0
    success_count: int = 0
    generated_docx_paths: list[str] = field(default_factory=list)
    generated_pdf_paths: list[str] = field(default_factory=list)
    last_certificate_number: str | None = None
    log_path: str = ""
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ExcelPreview:
    columns: list[str] = field(default_factory=list)
    row_count: int = 0

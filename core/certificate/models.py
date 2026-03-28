from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


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
    certificate_type: str = "certificato"
    category: str = ""
    export_pdf: bool = False
    pdf_timeout_seconds: int = 300
    mappings: list[MappingEntry] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "excel_path": self.excel_path,
            "template_path": self.template_path,
            "output_dir": self.output_dir,
            "license_path": self.license_path,
            "certificate_type": self.certificate_type,
            "category": self.category,
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

        return cls(
            excel_path=str(payload.get("excel_path", "")).strip(),
            template_path=str(payload.get("template_path", "")).strip(),
            output_dir=str(payload.get("output_dir", "")).strip(),
            license_path=str(payload.get("license_path", "")).strip(),
            certificate_type=str(payload.get("certificate_type", "certificato")).strip() or "certificato",
            category=str(payload.get("category", "")).strip(),
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

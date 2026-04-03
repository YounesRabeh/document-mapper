from __future__ import annotations

import tempfile
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from core.certificate.excel_service import ExcelDataService, normalize_column_name
from core.certificate.models import GenerationResult, MappingEntry, ProjectSession


class FakeExcelService:
    def __init__(self, dataframe: pd.DataFrame | None = None):
        self.dataframe = (
            dataframe if dataframe is not None else pd.DataFrame([{"NAME": "Ada", "LASTNAME": "Lovelace"}])
        )

    def inspect(self, _excel_path: str):
        return SimpleNamespace(columns=[str(column) for column in self.dataframe.columns], row_count=len(self.dataframe.index))

    def read_dataframe(self, _excel_path: str) -> pd.DataFrame:
        return self.dataframe.copy()

    def build_column_lookup(self, columns: list[str]) -> dict[str, str]:
        return {normalize_column_name(column): column for column in columns}

    def validate_mappings(self, columns: list[str], mappings: list[MappingEntry]) -> list[str]:
        return ExcelDataService().validate_mappings(columns, mappings)

    def clear_cache(self, _excel_path: str | None = None):
        return None


class FakeGenerator:
    def __init__(self, _excel_service=None, result: GenerationResult | None = None):
        self.result = result or GenerationResult(
            total_rows=1,
            success_count=1,
            generated_docx_paths=[],
            generated_pdf_paths=[],
            log_path="",
            errors=[],
        )

    def validate_session(self, session: ProjectSession) -> list[str]:
        errors: list[str] = []
        if not session.excel_path:
            errors.append("Select an Excel workbook.")
        if not session.template_path:
            errors.append("Select a project template or set a template override.")
        if not session.output_dir:
            errors.append("Choose an output folder.")
        if not session.output_naming_schema.strip():
            errors.append("Set an output naming schema before continuing.")
        if not session.placeholder_delimiter.strip():
            errors.append("Set a placeholder delimiter before continuing.")
        elif (
            session.detected_placeholder_delimiter.strip() != session.placeholder_delimiter.strip()
            or session.detected_placeholder_count <= 0
        ):
            errors.append("Refresh and detect at least one placeholder before continuing.")
        if not session.mappings:
            errors.append("Add at least one placeholder mapping.")
        for index, mapping in enumerate(session.mappings, start=1):
            if not mapping.placeholder.strip():
                errors.append(f"Mapping row {index} is missing a placeholder.")
            if not mapping.column_name.strip():
                errors.append(f"Mapping row {index} is missing an Excel column.")
        return errors


class FakeSessionStore:
    def __init__(self):
        self.session: ProjectSession | None = None
        self.loaded_session: ProjectSession | None = None
        self.last_session: ProjectSession | None = None
        self.saved_sessions: list[ProjectSession] = []
        self.save_last_session_hook = None

    def load_last_session(self):
        if self.last_session is not None:
            return self.last_session.clone()
        return ProjectSession()

    def save_last_session(self, session):
        if callable(self.save_last_session_hook):
            self.save_last_session_hook(session.clone())
        self.session = session.clone()
        self.saved_sessions.append(self.session.clone())
        return Path(tempfile.gettempdir()) / "last_session.json"

    def save(self, session, path):
        self.session = session.clone()
        resolved = Path(path)
        if resolved.suffix.lower() == ".json":
            return resolved
        return resolved / "project.json"

    def load(self, _path):
        if self.loaded_session is not None:
            session = self.loaded_session.clone()
        else:
            session = ProjectSession()
        session.template_path = self.resolve_effective_template_path(session, None)
        return session

    def resolve_effective_template_path(self, session: ProjectSession, _project_dir):
        if session.template_override_path:
            return session.template_override_path
        selected_entry = session.selected_template_entry()
        if selected_entry is not None:
            if selected_entry.source_path:
                return selected_entry.source_path
            if selected_entry.relative_path:
                return selected_entry.relative_path
        return session.template_path


class FakeDocument:
    license_value = None

    def __init__(self):
        self.replacements: list[tuple[str, str]] = []
        self.template_path = None

    def LoadFromFile(self, path: str):
        self.template_path = path

    def Replace(self, placeholder: str, value: str, _whole_word: bool, _case_sensitive: bool):
        self.replacements.append((placeholder, value))

    def SaveToFile(self, path: str, _file_format):
        Path(path).write_text("generated", encoding="utf-8")

    def Close(self):
        return None

    @classmethod
    def SetLicense(cls, path: str):
        cls.license_value = path


def fake_spire_dependencies():
    return FakeDocument, SimpleNamespace(Docx2016="Docx2016")

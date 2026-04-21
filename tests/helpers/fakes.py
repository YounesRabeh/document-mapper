from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from core.mapping.excel_service import ExcelDataService, normalize_column_name
from core.mapping.generator import GenerationCancelledError
from core.mapping.models import GenerationResult, MappingEntry, ProjectSession


class FakeExcelService:
    """Test double for ExcelDataService returning predictable workbook data."""

    def __init__(self, dataframe: pd.DataFrame | None = None):
        self.dataframe = (
            dataframe if dataframe is not None else pd.DataFrame([{"NAME": "Ada", "LASTNAME": "Lovelace"}])
        )

    def inspect(self, _excel_path: str):
        """Return preview metadata for the fake dataframe."""
        return SimpleNamespace(columns=[str(column) for column in self.dataframe.columns], row_count=len(self.dataframe.index))

    def read_dataframe(self, _excel_path: str) -> pd.DataFrame:
        """Return a copy of the fake dataframe."""
        return self.dataframe.copy()

    def build_column_lookup(self, columns: list[str]) -> dict[str, str]:
        """Build normalized lookup map from provided column names."""
        return {normalize_column_name(column): column for column in columns}

    def validate_mappings(self, columns: list[str], mappings: list[MappingEntry]) -> list[str]:
        """Reuse real mapping validation logic for fake service tests."""
        return ExcelDataService().validate_mappings(columns, mappings)

    def clear_cache(self, _excel_path: str | None = None):
        """No-op cache clear for fake service."""
        return None


class FakeGenerator:
    """Test double for DocumentGenerator with configurable result payload."""

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
        """Perform lightweight validation checks used by GUI tests."""
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

    def validate_session_inputs(self, session: ProjectSession) -> list[str]:
        """Match DocumentGenerator fast pre-check API used by GeneratePage."""
        return self.validate_session(session)

    def generate(self, _session: ProjectSession, progress_callback=None, cancel_requested=None) -> GenerationResult:
        """Return the configured result while honoring the runtime generator API."""
        if callable(cancel_requested) and cancel_requested():
            raise GenerationCancelledError("Generation cancelled.")
        if callable(progress_callback):
            progress_callback("INFO | Fake generation finished.")
        return self.result


class FakeSessionStore:
    """In-memory session store fake used by window and persistence tests."""

    def __init__(self):
        self.session: ProjectSession | None = None
        self.loaded_session: ProjectSession | None = None
        self.last_session: ProjectSession | None = None
        self.saved_sessions: list[ProjectSession] = []
        self.save_last_session_hook = None

    def load_last_session(self):
        """Return cloned last session or a default empty session."""
        if self.last_session is not None:
            return self.last_session.clone()
        return ProjectSession()

    def save_last_session(self, session):
        """Save last session snapshot in memory and optional hook."""
        if callable(self.save_last_session_hook):
            self.save_last_session_hook(session.clone())
        self.session = session.clone()
        self.saved_sessions.append(self.session.clone())
        return Path(tempfile.gettempdir()) / "last_session.json"

    def save(self, session, path, source_project_dir=None):
        """Persist project payload to a temporary JSON file for tests."""
        del source_project_dir
        self.session = session.clone()
        self.loaded_session = self.session.clone()
        resolved = Path(path)
        if resolved.suffix.lower() == ".json":
            project_json = resolved
        else:
            project_json = resolved / "project.json"
        project_json.parent.mkdir(parents=True, exist_ok=True)
        project_json.write_text(json.dumps(self.session.to_project_dict(), indent=2), encoding="utf-8")
        return project_json

    def load(self, _path):
        """Load a cloned saved session and resolve effective template path."""
        if self.loaded_session is not None:
            session = ProjectSession.from_project_dict(self.loaded_session.to_project_dict())
        else:
            session = ProjectSession()
        session.template_path = self.resolve_effective_template_path(session, None)
        return session

    def resolve_effective_template_path(self, session: ProjectSession, _project_dir):
        """Resolve active template path using override/entry/session precedence."""
        if session.template_override_path:
            return session.template_override_path
        selected_entry = session.selected_template_entry()
        if selected_entry is not None:
            if selected_entry.source_path:
                return selected_entry.source_path
            if selected_entry.relative_path:
                return selected_entry.relative_path
        return session.template_path


class FakeLastSessionPersistenceService:
    """Synchronous fake for async last-session persistence service."""

    def __init__(self, session_store):
        self._session_store = session_store
        self._latest_snapshot: ProjectSession | None = None

    def enqueue(self, snapshot: ProjectSession):
        """Persist snapshot immediately in the backing fake store."""
        self._latest_snapshot = snapshot.clone()
        self._session_store.save_last_session(self._latest_snapshot.clone())

    def latest_snapshot(self) -> ProjectSession | None:
        """Return the latest persisted snapshot clone."""
        if self._latest_snapshot is None:
            return None
        return self._latest_snapshot.clone()

    def flush(self, timeout: float | None = None) -> bool:
        """Fake flush always succeeds immediately."""
        del timeout
        return True

    def flush_and_stop(self, timeout: float | None = None) -> bool:
        """Fake flush+stop always succeeds immediately."""
        del timeout
        return True


class FakeDocument:
    """Minimal Spire.Document stand-in used by generator tests."""

    license_value = None

    def __init__(self):
        self.replacements: list[tuple[str, str]] = []
        self.template_path = None

    def LoadFromFile(self, path: str):
        """Record template path used for generation."""
        self.template_path = path

    def Replace(self, placeholder: str, value: str, _whole_word: bool, _case_sensitive: bool):
        """Record placeholder replacement calls."""
        self.replacements.append((placeholder, value))

    def SaveToFile(self, path: str, _file_format):
        """Write a simple generated marker file."""
        Path(path).write_text("generated", encoding="utf-8")

    def Close(self):
        """No-op close method for API compatibility."""
        return None

    @classmethod
    def SetLicense(cls, path: str):
        """Record license path passed by generator logic."""
        cls.license_value = path


def fake_spire_dependencies():
    """Return fake Spire dependencies tuple used in patching."""
    return FakeDocument, SimpleNamespace(Docx2016="Docx2016")

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.mapping.models import GenerationResult, ProjectSession


@dataclass(slots=True)
class ProjectDocument:
    """Track active session state, last result, and saved/dirty document snapshot."""

    session: ProjectSession = field(default_factory=ProjectSession)
    project_path: str | None = None
    last_result: GenerationResult = field(default_factory=GenerationResult)
    _saved_snapshot: dict[str, Any] | None = field(default=None, init=False, repr=False)
    _saved_session: ProjectSession | None = field(default=None, init=False, repr=False)

    def __post_init__(self):
        self.session = self.session.clone()
        self.project_path = self._normalize_project_path(self.project_path)
        self.last_result = GenerationResult(
            total_rows=self.last_result.total_rows,
            success_count=self.last_result.success_count,
            generated_docx_paths=list(self.last_result.generated_docx_paths),
            generated_pdf_paths=list(self.last_result.generated_pdf_paths),
            log_path=self.last_result.log_path,
            errors=list(self.last_result.errors),
        )
        self.mark_saved()

    @property
    def project_dir(self) -> Path | None:
        """Return the resolved project directory, if available."""
        if not self.project_path:
            return None
        return Path(self.project_path).expanduser().resolve()

    @property
    def is_dirty(self) -> bool:
        """Return True when current session state differs from saved snapshot."""
        return self._saved_snapshot is None or self.snapshot() != self._saved_snapshot

    def snapshot(self) -> dict[str, Any]:
        """Return a serializable snapshot of the current project session."""
        return self.session.to_project_dict()

    def load(self, session: ProjectSession, project_path: str | Path | None = None):
        """Load a session as the current saved project state."""
        self.session = session.clone()
        self.project_path = self._normalize_project_path(project_path)
        self.last_result = GenerationResult()
        self.mark_saved()

    def activate(self, session: ProjectSession, project_path: str | Path | None = None, *, saved: bool):
        """Activate a session as current state and optionally mark it as saved."""
        self.session = session.clone()
        self.project_path = self._normalize_project_path(project_path)
        self.last_result = GenerationResult()
        if saved:
            self.mark_saved()
        else:
            self._saved_snapshot = None
            self._saved_session = None

    def mark_saved(self):
        """Capture the current session as the saved baseline snapshot."""
        self._saved_snapshot = self.snapshot()
        self._saved_session = self.session.clone()

    def saved_session(self) -> ProjectSession | None:
        """Return a clone of the saved baseline session, if present."""
        if self._saved_session is None:
            return None
        return self._saved_session.clone()

    @staticmethod
    def _normalize_project_path(project_path: str | Path | None) -> str | None:
        if not project_path:
            return None
        return str(Path(project_path).expanduser().resolve())

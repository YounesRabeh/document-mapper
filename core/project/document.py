from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.mapping.models import GenerationResult, ProjectSession


@dataclass(slots=True)
class ProjectDocument:
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
        if not self.project_path:
            return None
        return Path(self.project_path).expanduser().resolve()

    @property
    def is_dirty(self) -> bool:
        return self._saved_snapshot is None or self.snapshot() != self._saved_snapshot

    def snapshot(self) -> dict[str, Any]:
        return self.session.to_project_dict()

    def load(self, session: ProjectSession, project_path: str | Path | None = None):
        self.session = session.clone()
        self.project_path = self._normalize_project_path(project_path)
        self.last_result = GenerationResult()
        self.mark_saved()

    def activate(self, session: ProjectSession, project_path: str | Path | None = None, *, saved: bool):
        self.session = session.clone()
        self.project_path = self._normalize_project_path(project_path)
        self.last_result = GenerationResult()
        if saved:
            self.mark_saved()
        else:
            self._saved_snapshot = None
            self._saved_session = None

    def mark_saved(self):
        self._saved_snapshot = self.snapshot()
        self._saved_session = self.session.clone()

    def saved_session(self) -> ProjectSession | None:
        if self._saved_session is None:
            return None
        return self._saved_session.clone()

    @staticmethod
    def _normalize_project_path(project_path: str | Path | None) -> str | None:
        if not project_path:
            return None
        return str(Path(project_path).expanduser().resolve())

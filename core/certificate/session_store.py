from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import shutil

from core.certificate.models import (
    DEFAULT_IMPORTED_TEMPLATE_TYPE,
    DEFAULT_IMPORTED_TEMPLATE_NAME,
    MappingEntry,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
    normalize_template_name,
)
from core.util.app_paths import AppPaths


class ProjectSessionStore:
    last_session_filename = "last_session.json"
    project_filename = "project.json"
    managed_templates_dirname = "templates"

    def __init__(self, base_dir: str | Path | None = None):
        self._default_location = base_dir is None
        if base_dir is None:
            base_dir = AppPaths.state_dir()
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        if self._default_location:
            self._migrate_legacy_last_session()

    @property
    def last_session_path(self) -> Path:
        return self.base_dir / self.last_session_filename

    def save(self, session: ProjectSession, path: str | Path) -> Path:
        project_dir, project_json_path = self._resolve_project_destination(path)
        prepared_session = session.clone()
        self._materialize_project_templates(prepared_session, project_dir)
        prepared_session.template_path = self.resolve_effective_template_path(prepared_session, project_dir)
        self._write_json(prepared_session, project_json_path)
        return project_json_path

    def load(self, path: str | Path) -> ProjectSession:
        project_json_path, project_dir = self._resolve_project_source(path)
        session = self._load_json(project_json_path)
        session.template_path = self.resolve_effective_template_path(session, project_dir)
        return session

    def load_legacy_files(
        self,
        config_path: str | Path = "config.json",
        setup_path: str | Path = "SETUP.json",
    ) -> ProjectSession:
        mapping_file = Path(config_path).expanduser().resolve()
        paths_file = Path(setup_path).expanduser().resolve()

        if not mapping_file.exists():
            raise FileNotFoundError(f"Legacy mapping file not found: {mapping_file}")
        if not paths_file.exists():
            raise FileNotFoundError(f"Legacy setup file not found: {paths_file}")

        with open(mapping_file, "r", encoding="utf-8") as handle:
            placeholder_mapping = json.load(handle)
        with open(paths_file, "r", encoding="utf-8") as handle:
            paths = json.load(handle)

        if not isinstance(placeholder_mapping, dict):
            raise ValueError("Legacy mapping file must be a JSON object of placeholder-to-column pairs.")
        if not isinstance(paths, dict):
            raise ValueError("Legacy setup file must be a JSON object.")

        try:
            timeout = int(paths.get("toPDF_timeout", 300) or 300)
        except (TypeError, ValueError):
            timeout = 300

        legacy_template_path = str(paths.get("template_path", "")).strip()
        imported_type = ProjectTemplateType(DEFAULT_IMPORTED_TEMPLATE_TYPE)
        imported_entry = ProjectTemplateEntry(
            display_name=DEFAULT_IMPORTED_TEMPLATE_NAME,
            type_name=imported_type.name,
            source_path=legacy_template_path,
            is_managed=False,
        )

        return ProjectSession(
            excel_path=str(paths.get("excel_path", "")).strip(),
            template_path=legacy_template_path,
            output_dir=str(paths.get("output_dir", "")).strip(),
            license_path=str(paths.get("license_path", "")).strip(),
            selected_template_type=imported_type.name,
            selected_template=imported_entry.id,
            template_types=[imported_type],
            templates=[imported_entry],
            placeholder_delimiter="",
            export_pdf=bool(paths.get("toPDF", False)),
            pdf_timeout_seconds=max(1, timeout),
            mappings=[
                MappingEntry(placeholder=str(placeholder).strip(), column_name=str(column).strip())
                for placeholder, column in placeholder_mapping.items()
            ],
        )

    def save_last_session(self, session: ProjectSession) -> Path:
        return self._write_json(session, self.last_session_path)

    def load_last_session(self) -> ProjectSession:
        if not self.last_session_path.exists():
            return ProjectSession()
        try:
            return self._load_json(self.last_session_path)
        except (json.JSONDecodeError, OSError, ValueError, TypeError) as exc:
            self._quarantine_invalid_last_session(exc)
            return ProjectSession()

    def _write_json(self, session: ProjectSession, path: Path) -> Path:
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w", encoding="utf-8") as handle:
            json.dump(session.to_dict(), handle, indent=2, ensure_ascii=True)
        return destination

    def _load_json(self, path: str | Path) -> ProjectSession:
        source = Path(path).expanduser().resolve()
        with open(source, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return ProjectSession.from_dict(payload)

    def _resolve_project_destination(self, path: str | Path) -> tuple[Path, Path]:
        destination = Path(path).expanduser().resolve()
        if destination.suffix.lower() == ".json":
            project_dir = destination.parent
            project_json_path = destination
        else:
            project_dir = destination
            project_json_path = project_dir / self.project_filename
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir, project_json_path

    def _resolve_project_source(self, path: str | Path) -> tuple[Path, Path]:
        source = Path(path).expanduser().resolve()
        if source.is_dir():
            project_dir = source
            project_json_path = source / self.project_filename
        else:
            project_json_path = source
            project_dir = source.parent
        if not project_json_path.exists():
            raise FileNotFoundError(f"Project file not found: {project_json_path}")
        return project_json_path, project_dir

    def _materialize_project_templates(self, session: ProjectSession, project_dir: Path):
        templates_dir = project_dir / self.managed_templates_dirname
        templates_dir.mkdir(parents=True, exist_ok=True)
        used_relative_paths = {entry.relative_path for entry in session.templates if entry.relative_path}

        for entry in session.templates:
            if entry.is_managed and entry.relative_path and (project_dir / entry.relative_path).exists():
                continue
            source_path = Path(entry.source_path).expanduser().resolve() if entry.source_path else None
            if source_path is None or not source_path.exists():
                continue
            relative_path = self._unique_managed_relative_path(
                used_relative_paths,
                source_path,
                entry.display_name or normalize_template_name(source_path.stem),
            )
            target_path = project_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            entry.relative_path = relative_path.as_posix()
            entry.is_managed = True
            used_relative_paths.add(entry.relative_path)

    def _unique_managed_relative_path(
        self,
        used_relative_paths: set[str],
        source_path: Path,
        display_name: str,
    ) -> Path:
        safe_stem = self._sanitize_template_filename(display_name or source_path.stem)
        suffix = source_path.suffix or ".docx"
        candidate = Path(self.managed_templates_dirname) / f"{safe_stem}{suffix}"
        counter = 2
        while candidate.as_posix() in used_relative_paths:
            candidate = Path(self.managed_templates_dirname) / f"{safe_stem}_{counter}{suffix}"
            counter += 1
        return candidate

    def resolve_effective_template_path(self, session: ProjectSession, project_dir: Path | None) -> str:
        if session.template_override_path:
            override_path = Path(session.template_override_path).expanduser().resolve()
            return str(override_path)

        selected_entry = session.selected_template_entry()
        if selected_entry is not None:
            if selected_entry.is_managed and selected_entry.relative_path and project_dir is not None:
                return str((project_dir / selected_entry.relative_path).resolve())
            if selected_entry.source_path:
                return str(Path(selected_entry.source_path).expanduser().resolve())

        return str(Path(session.template_path).expanduser().resolve()) if session.template_path else ""

    def _sanitize_template_filename(self, value: str) -> str:
        sanitized = normalize_template_name(value)
        sanitized = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in sanitized)
        sanitized = sanitized.strip("._")
        return sanitized or "template"

    def _migrate_legacy_last_session(self):
        if self.last_session_path.exists():
            return

        legacy_path = AppPaths.legacy_last_session_path(self.last_session_filename)
        if not legacy_path.exists():
            return

        try:
            session = self._load_json(legacy_path)
        except (json.JSONDecodeError, OSError, ValueError, TypeError) as exc:
            self._quarantine_legacy_last_session(legacy_path, exc)
            return

        self.save_last_session(session)
        try:
            legacy_path.unlink()
        except OSError:
            pass

    def _quarantine_invalid_last_session(self, _exc: Exception):
        quarantine_path = self._invalid_session_backup_path(self.last_session_path)
        self._safe_move_to_quarantine(self.last_session_path, quarantine_path)

    def _quarantine_legacy_last_session(self, legacy_path: Path, _exc: Exception):
        quarantine_path = self._invalid_session_backup_path(legacy_path)
        self._safe_move_to_quarantine(legacy_path, quarantine_path)

    def _invalid_session_backup_path(self, source: Path) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return source.with_name(f"{source.stem}.invalid-{timestamp}{source.suffix}")

    def _safe_move_to_quarantine(self, source: Path, destination: Path):
        try:
            shutil.move(str(source), str(destination))
        except OSError:
            try:
                source.unlink(missing_ok=True)
            except OSError:
                pass

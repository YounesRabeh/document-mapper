from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import shutil

from core.certificate.models import (
    DEFAULT_CERTIFICATE_TYPE,
    MappingEntry,
    ProjectSession,
    normalize_certificate_type,
)
from core.util.app_paths import AppPaths


class ProjectSessionStore:
    last_session_filename = "last_session.json"

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
        destination = Path(path).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        with open(destination, "w", encoding="utf-8") as handle:
            json.dump(session.to_dict(), handle, indent=2, ensure_ascii=True)
        return destination

    def load(self, path: str | Path) -> ProjectSession:
        source = Path(path).expanduser().resolve()
        with open(source, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        return ProjectSession.from_dict(payload)

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

        return ProjectSession(
            excel_path=str(paths.get("excel_path", "")).strip(),
            template_path=str(paths.get("template_path", "")).strip(),
            output_dir=str(paths.get("output_dir", "")).strip(),
            license_path=str(paths.get("license_path", "")).strip(),
            certificate_type=normalize_certificate_type(paths.get("certificate_type", DEFAULT_CERTIFICATE_TYPE)),
            placeholder_delimiter="",
            export_pdf=bool(paths.get("toPDF", False)),
            pdf_timeout_seconds=max(1, timeout),
            mappings=[
                MappingEntry(placeholder=str(placeholder).strip(), column_name=str(column).strip())
                for placeholder, column in placeholder_mapping.items()
            ],
        )

    def save_last_session(self, session: ProjectSession) -> Path:
        return self.save(session, self.last_session_path)

    def load_last_session(self) -> ProjectSession:
        if not self.last_session_path.exists():
            return ProjectSession()
        try:
            return self.load(self.last_session_path)
        except (json.JSONDecodeError, OSError, ValueError, TypeError) as exc:
            self._quarantine_invalid_last_session(exc)
            return ProjectSession()

    def _migrate_legacy_last_session(self):
        if self.last_session_path.exists():
            return

        legacy_path = AppPaths.legacy_last_session_path(self.last_session_filename)
        if not legacy_path.exists():
            return

        try:
            session = self.load(legacy_path)
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

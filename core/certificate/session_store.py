from __future__ import annotations

import json
from pathlib import Path

from core.certificate.models import (
    DEFAULT_CERTIFICATE_TYPE,
    MappingEntry,
    ProjectSession,
    normalize_certificate_type,
)
from core.util.resources import Resources


class ProjectSessionStore:
    last_session_filename = "last_session.json"

    def __init__(self, base_dir: str | Path | None = None):
        if base_dir is None:
            configured_temp = getattr(Resources, "temp", None)
            base_dir = configured_temp or (Path.cwd() / "resources" / "temp")
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

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
        return self.load(self.last_session_path)

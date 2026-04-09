from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import zipfile

from core.mapping.models import GenerationResult

ARCHIVE_FORMAT_FOLDER = "folder"
ARCHIVE_FORMAT_ZIP = "zip"


@dataclass(slots=True)
class ArchiveCreationError(Exception):
    """Domain error raised when archive validation or creation fails."""

    code: str
    details: str = ""

    def __str__(self) -> str:
        return f"{self.code}: {self.details}" if self.details else self.code


class OutputArchiveService:
    """Create folder/ZIP archives for generated outputs."""

    def available_formats(self) -> list[str]:
        """Return archive formats supported by this runtime."""
        return [ARCHIVE_FORMAT_FOLDER, ARCHIVE_FORMAT_ZIP]

    def build_target_path(self, root_dir: str | Path, run_name: str, archive_format: str) -> Path:
        """Resolve the final archive target path for a run and format."""
        archive_root = self._resolve_root_dir(root_dir)
        normalized_run_name = self._normalize_run_name(run_name)
        if not normalized_run_name:
            raise ArchiveCreationError("invalid_run_name")

        if archive_format == ARCHIVE_FORMAT_FOLDER:
            return archive_root / normalized_run_name
        if archive_format == ARCHIVE_FORMAT_ZIP:
            return archive_root / f"{normalized_run_name}.zip"
        raise ArchiveCreationError("unsupported_format", archive_format)

    def create_archive(
        self,
        result: GenerationResult,
        root_dir: str | Path,
        run_name: str,
        archive_format: str,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Create an output archive from a generation result and return its path."""
        entries = self._collect_entries(result)
        target_path = self.build_target_path(root_dir, run_name, archive_format)

        if target_path.exists() and not overwrite:
            raise ArchiveCreationError("already_exists", str(target_path))
        if target_path.exists() and overwrite:
            self._remove_existing_target(target_path)

        if archive_format == ARCHIVE_FORMAT_FOLDER:
            self._create_folder_archive(entries, target_path)
            return target_path

        if archive_format == ARCHIVE_FORMAT_ZIP:
            self._create_zip_archive(entries, target_path)
            return target_path

        raise ArchiveCreationError("unsupported_format", archive_format)

    def create_zip_archive(
        self,
        result: GenerationResult,
        root_dir: str | Path,
        run_name: str,
        *,
        overwrite: bool = False,
    ) -> Path:
        """Shortcut to create a ZIP archive for a generation result."""
        return self.create_archive(
            result,
            root_dir,
            run_name,
            ARCHIVE_FORMAT_ZIP,
            overwrite=overwrite,
        )

    def _collect_entries(self, result: GenerationResult) -> list[tuple[Path, Path]]:
        if result.errors:
            raise ArchiveCreationError("has_errors")

        entries: list[tuple[Path, Path]] = []
        used_names: set[str] = set()
        entries.extend(self._entries_for_category(result.generated_docx_paths, "docx", used_names))
        entries.extend(self._entries_for_category(result.generated_pdf_paths, "pdf", used_names))
        if not entries:
            raise ArchiveCreationError("no_files")
        return entries

    def _entries_for_category(
        self,
        paths: list[str],
        category: str,
        used_names: set[str],
    ) -> list[tuple[Path, Path]]:
        category_entries: list[tuple[Path, Path]] = []
        for raw_path in paths:
            normalized_path = str(raw_path or "").strip()
            if not normalized_path:
                continue
            source_path = Path(normalized_path)
            if not source_path.is_file():
                raise ArchiveCreationError("missing_source_file", str(source_path))
            archive_name = self._dedupe_archive_name(category, source_path.name, used_names)
            category_entries.append((source_path, archive_name))
        return category_entries

    def _dedupe_archive_name(self, category: str, file_name: str, used_names: set[str]) -> Path:
        candidate = Path(category) / file_name
        candidate_key = candidate.as_posix().casefold()
        if candidate_key not in used_names:
            used_names.add(candidate_key)
            return candidate

        suffix = Path(file_name).suffix
        stem = Path(file_name).stem
        index = 2
        while True:
            renamed_candidate = Path(category) / f"{stem}_{index}{suffix}"
            renamed_key = renamed_candidate.as_posix().casefold()
            if renamed_key not in used_names:
                used_names.add(renamed_key)
                return renamed_candidate
            index += 1

    def _resolve_root_dir(self, root_dir: str | Path) -> Path:
        raw_root = str(root_dir or "").strip()
        if not raw_root:
            raise ArchiveCreationError("invalid_root")
        archive_root = Path(raw_root).expanduser()
        if archive_root.exists() and not archive_root.is_dir():
            raise ArchiveCreationError("invalid_root", str(archive_root))
        try:
            archive_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise ArchiveCreationError("invalid_root", str(exc)) from exc
        return archive_root

    def _remove_existing_target(self, target_path: Path):
        try:
            if target_path.is_dir():
                shutil.rmtree(target_path)
            else:
                target_path.unlink()
        except OSError as exc:
            raise ArchiveCreationError("write_failed", str(exc)) from exc

    def _create_folder_archive(self, entries: list[tuple[Path, Path]], target_path: Path):
        try:
            target_path.mkdir(parents=True, exist_ok=False)
            for source_path, relative_path in entries:
                destination_path = target_path / relative_path
                destination_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination_path)
        except OSError as exc:
            raise ArchiveCreationError("write_failed", str(exc)) from exc

    def _create_zip_archive(self, entries: list[tuple[Path, Path]], target_path: Path):
        temp_archive_path = target_path.with_name(f"{target_path.name}.tmp")
        if temp_archive_path.exists():
            temp_archive_path.unlink()
        try:
            with zipfile.ZipFile(temp_archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for source_path, archive_name in entries:
                    archive.write(source_path, arcname=archive_name.as_posix())
            temp_archive_path.replace(target_path)
        except OSError as exc:
            raise ArchiveCreationError("write_failed", str(exc)) from exc

    def _normalize_run_name(self, run_name: str) -> str:
        raw_value = str(run_name or "").strip()
        lower = raw_value.lower()
        if lower.endswith(".zip"):
            raw_value = raw_value[:-4].strip()
        if not raw_value:
            return ""
        normalized = re.sub(r"\s+", "_", raw_value)
        normalized = re.sub(r"[^\w.-]+", "_", normalized, flags=re.ASCII)
        normalized = re.sub(r"_+", "_", normalized).strip("._-")
        return normalized

from __future__ import annotations

import os
import re
import subprocess
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from core.mapping.excel_service import ExcelDataService, normalize_column_name
from core.mapping.models import (
    GenerationResult,
    MappingEntry,
    ProjectSession,
    normalize_output_naming_schema,
    normalize_placeholder_delimiter,
)
from core.util.app_paths import AppPaths
from core.util.logger import Logger

LogCallback = Callable[[str], None]
OUTPUT_SCHEMA_TOKEN_PATTERN = re.compile(r"\{([^{}]+)\}")
OUTPUT_SCHEMA_BUILTINS = {
    "ROW",
    "TEMPLATE",
}
FIRST_NAME_ALIASES = (
    normalize_column_name("NAME"),
    normalize_column_name("NOME"),
)
LAST_NAME_ALIASES = (
    normalize_column_name("LASTNAME"),
    normalize_column_name("COGNOME"),
)
DATE_ALIASES = frozenset(
    (
        normalize_column_name("COURSE_DATE"),
        normalize_column_name("DATE"),
        normalize_column_name("DATA"),
    )
)
UPPERCASE_TEXT_ALIASES = frozenset((*FIRST_NAME_ALIASES, *LAST_NAME_ALIASES))


class DocumentGenerator:
    def __init__(
        self,
        excel_service: ExcelDataService | None = None,
        process_runner: Callable[..., subprocess.CompletedProcess] | None = None,
    ):
        self.excel_service = excel_service or ExcelDataService()
        self.process_runner = process_runner or subprocess.run

    def validate_session(self, session: ProjectSession) -> list[str]:
        errors: list[str] = []

        if not session.excel_path:
            errors.append("Select an Excel workbook.")
        elif not Path(session.excel_path).exists():
            errors.append(f"Excel file not found: {session.excel_path}")

        if not session.template_path:
            errors.append("Select a project template or set a template override.")
        elif not Path(session.template_path).exists():
            errors.append(f"Template file not found: {session.template_path}")

        if not session.output_dir:
            errors.append("Choose an output folder.")
        else:
            output_dir_error = self._validate_output_dir(session.output_dir)
            if output_dir_error:
                errors.append(f"Output folder is not writable: {output_dir_error}")

        if session.license_path and not Path(session.license_path).exists():
            errors.append(f"License file not found: {session.license_path}")

        if not session.placeholder_delimiter.strip():
            errors.append("Set a placeholder delimiter before continuing.")
        else:
            active_delimiter = normalize_placeholder_delimiter(session.placeholder_delimiter)
            detected_delimiter = normalize_placeholder_delimiter(session.detected_placeholder_delimiter)
            if detected_delimiter != active_delimiter or session.detected_placeholder_count <= 0:
                errors.append("Refresh and detect at least one placeholder before continuing.")

        if not normalize_output_naming_schema(session.output_naming_schema):
            errors.append("Set an output naming schema before continuing.")

        if not session.mappings:
            errors.append("Add at least one placeholder mapping.")

        if errors:
            return errors

        try:
            preview = self.excel_service.inspect(session.excel_path)
        except Exception as exc:
            return [f"Cannot read Excel workbook: {exc}"]

        errors.extend(self.excel_service.validate_mappings(preview.columns, session.mappings))
        errors.extend(self._validate_output_naming_schema(session.output_naming_schema, preview.columns))
        return errors

    def existing_output_conflicts(self, session: ProjectSession) -> list[str]:
        if not session.output_dir or not session.excel_path:
            return []
        if not Path(session.excel_path).exists():
            return []

        try:
            dataframe = self.excel_service.read_dataframe(session.excel_path)
        except Exception:
            return []

        output_root = Path(session.output_dir).resolve()
        docx_dir = output_root / "docx"
        pdf_dir = output_root / "pdf"
        column_lookup = self.excel_service.build_column_lookup([str(column) for column in dataframe.columns])

        used_output_basenames: dict[str, int] = {}
        conflicts: list[str] = []
        seen: set[str] = set()

        for index, row in dataframe.iterrows():
            output_path = self._build_docx_output_path(
                session,
                row,
                index,
                docx_dir,
                column_lookup,
                used_output_basenames,
            )
            if output_path.exists():
                key = str(output_path)
                if key not in seen:
                    conflicts.append(key)
                    seen.add(key)

            if session.export_pdf:
                pdf_path = pdf_dir / f"{output_path.stem}.pdf"
                if pdf_path.exists():
                    key = str(pdf_path)
                    if key not in seen:
                        conflicts.append(key)
                        seen.add(key)

        return conflicts

    def generate(
        self,
        session: ProjectSession,
        progress_callback: LogCallback | None = None,
    ) -> GenerationResult:
        errors = self.validate_session(session)
        log_path = self._resolve_log_path(session)
        self._initialize_log(log_path)

        if errors:
            for error in errors:
                self._write_log(log_path, f"ERROR | {error}", progress_callback)
            return GenerationResult(log_path=str(log_path), errors=errors)

        dataframe = self.excel_service.read_dataframe(session.excel_path)
        total_rows = len(dataframe.index)
        self._write_log(log_path, f"INFO | Loaded {total_rows} rows from workbook.", progress_callback)

        docx_dir = Path(session.output_dir).resolve() / "docx"
        pdf_dir = Path(session.output_dir).resolve() / "pdf"
        docx_dir.mkdir(parents=True, exist_ok=True)
        if session.export_pdf:
            pdf_dir.mkdir(parents=True, exist_ok=True)

        column_lookup = self.excel_service.build_column_lookup([str(column) for column in dataframe.columns])
        generated_docx_paths: list[str] = []
        generated_pdf_paths: list[str] = []
        generation_errors: list[str] = []
        used_output_basenames: dict[str, int] = {}

        document_cls, file_format = self._load_spire_dependencies()
        licensed = self._activate_license(document_cls, session.license_path, log_path, progress_callback)

        for index, row in dataframe.iterrows():
            try:
                output_path = self._build_docx_output_path(
                    session,
                    row,
                    index,
                    docx_dir,
                    column_lookup,
                    used_output_basenames,
                )
                replacements = self._build_replacements(row, session.mappings, column_lookup)
                participant_name = self._participant_name(row, column_lookup, index)

                self._write_log(
                    log_path,
                    f"PROCESS | Generating document for {participant_name} ({index + 1}/{total_rows})",
                    progress_callback,
                )

                document = document_cls()
                document.LoadFromFile(session.template_path)
                for placeholder, value in replacements.items():
                    document.Replace(placeholder, value, False, True)
                document.SaveToFile(str(output_path), file_format.Docx2016)
                document.Close()

                if not licensed:
                    self._clean_docx_content(output_path)

                generated_docx_paths.append(str(output_path))
                self._write_log(log_path, f"SUCCESS | Created DOCX {output_path.name}", progress_callback)
            except Exception as exc:
                error = f"Failed to generate row {index + 1}: {exc}"
                generation_errors.append(error)
                self._write_log(log_path, f"ERROR | {error}", progress_callback)

        if session.export_pdf and generated_docx_paths:
            generated_pdf_paths = self._batch_convert_docx_to_pdf(
                generated_docx_paths,
                pdf_dir,
                session.pdf_timeout_seconds,
                log_path,
                progress_callback,
            )

        self._write_log(
            log_path,
            f"INFO | Generation complete: {len(generated_docx_paths)}/{total_rows} DOCX files created.",
            progress_callback,
        )

        return GenerationResult(
            total_rows=total_rows,
            success_count=len(generated_docx_paths),
            generated_docx_paths=generated_docx_paths,
            generated_pdf_paths=generated_pdf_paths,
            log_path=str(log_path),
            errors=generation_errors,
        )

    def _load_spire_dependencies(self):
        try:
            from spire.doc import Document, FileFormat
        except ImportError as exc:
            raise RuntimeError(
                "Spire.Doc is not installed. Install the runtime dependency before generating documents."
            ) from exc
        return Document, FileFormat

    def _activate_license(
        self,
        document_cls,
        license_path: str,
        log_path: Path,
        progress_callback: LogCallback | None,
    ) -> bool:
        if not license_path:
            self._write_log(log_path, "WARNING | Running without a Spire license.", progress_callback)
            return False
        try:
            document_cls.SetLicense(license_path)
            self._write_log(log_path, "SUCCESS | Spire license activated.", progress_callback)
            return True
        except Exception as exc:
            self._write_log(log_path, f"WARNING | Failed to activate license: {exc}", progress_callback)
            return False

    def _build_replacements(
        self,
        row: pd.Series,
        mappings: list[MappingEntry],
        column_lookup: dict[str, str],
    ) -> dict[str, str]:
        replacements: dict[str, str] = {}
        for mapping in mappings:
            normalized = normalize_column_name(mapping.column_name)
            column_name = column_lookup.get(normalized)
            if not column_name:
                continue
            value = row.get(column_name)
            replacements[mapping.placeholder] = self._format_cell_value(column_name, value)
        return replacements

    def _format_cell_value(self, column_name: str, value) -> str:
        if pd.isna(value) or value in (None, "", "NaT", "NaN"):
            return ""

        normalized = normalize_column_name(column_name)
        if normalized in DATE_ALIASES:
            return self._format_date_to_dd_mm_yyyy(value)
        if normalized in UPPERCASE_TEXT_ALIASES:
            return str(value).strip().upper()
        return str(value).strip()

    def _format_date_to_dd_mm_yyyy(self, value) -> str:
        if pd.isna(value) or value in (None, "", "NaT", "NaN"):
            return ""

        if isinstance(value, (pd.Timestamp, datetime, date)):
            return value.strftime("%d/%m/%Y")

        date_text = str(value).strip()
        parsers = (
            lambda raw: datetime.strptime(raw, "%Y-%m-%d"),
            lambda raw: datetime.strptime(raw, "%d/%m/%Y"),
            lambda raw: datetime.strptime(raw, "%d/%m/%y"),
            lambda raw: pd.to_datetime(raw).to_pydatetime(),
        )
        for parser in parsers:
            try:
                return parser(date_text).strftime("%d/%m/%Y")
            except (TypeError, ValueError):
                continue
        return date_text

    def _participant_name(
        self,
        row: pd.Series,
        column_lookup: dict[str, str],
        row_index: int,
    ) -> str:
        first_name = self._first_row_value(row, column_lookup, FIRST_NAME_ALIASES).upper()
        last_name = self._first_row_value(row, column_lookup, LAST_NAME_ALIASES).upper()
        full_name = " ".join(part for part in (first_name, last_name) if part).strip()
        return full_name or f"row-{row_index + 1}"

    def _build_docx_output_path(
        self,
        session: ProjectSession,
        row: pd.Series,
        row_index: int,
        output_dir: Path,
        column_lookup: dict[str, str],
        used_output_basenames: dict[str, int] | None = None,
    ) -> Path:
        basename = self._build_output_basename(session, row, row_index, column_lookup)
        if used_output_basenames is None:
            used_output_basenames = {}
        unique_basename = self._ensure_unique_output_basename(
            basename,
            used_output_basenames,
        )
        return output_dir / f"{unique_basename}.docx"

    def _build_output_basename(
        self,
        session: ProjectSession,
        row: pd.Series,
        row_index: int,
        column_lookup: dict[str, str],
    ) -> str:
        resolved_name = self._resolve_output_naming_schema(session, row, row_index, column_lookup)
        sanitized = self._sanitize_output_basename(resolved_name)
        if sanitized:
            return sanitized
        return self._sanitize_output_basename(f"row_{row_index + 1:03d}")

    def _resolve_output_naming_schema(
        self,
        session: ProjectSession,
        row: pd.Series,
        row_index: int,
        column_lookup: dict[str, str],
    ) -> str:
        schema = normalize_output_naming_schema(session.output_naming_schema)
        if not schema:
            return ""

        def replace_token(match: re.Match[str]) -> str:
            token = match.group(1).strip()
            return self._resolve_output_schema_token(session, row, row_index, column_lookup, token)

        return OUTPUT_SCHEMA_TOKEN_PATTERN.sub(replace_token, schema)

    def _resolve_output_schema_token(
        self,
        session: ProjectSession,
        row: pd.Series,
        row_index: int,
        column_lookup: dict[str, str],
        token: str,
    ) -> str:
        normalized = normalize_column_name(token)
        if normalized == "ROW":
            return str(row_index + 1)
        if normalized == "TEMPLATE":
            return session.active_template_name

        column_name = column_lookup.get(normalized)
        if not column_name:
            return ""
        value = row.get(column_name)
        return self._format_cell_value(column_name, value)

    def _validate_output_naming_schema(self, schema: str, columns: list[str]) -> list[str]:
        normalized_schema = normalize_output_naming_schema(schema)
        if not normalized_schema:
            return []

        column_lookup = self.excel_service.build_column_lookup(columns)
        errors: list[str] = []
        for token in self._extract_output_schema_tokens(normalized_schema):
            normalized_token = normalize_column_name(token)
            if normalized_token in OUTPUT_SCHEMA_BUILTINS:
                continue
            if normalized_token in column_lookup:
                continue
            errors.append(
                f"Output naming schema token '{token}' is not available as a workbook column or built-in value."
            )
        return errors

    def _extract_output_schema_tokens(self, schema: str) -> list[str]:
        tokens: list[str] = []
        seen: set[str] = set()
        for match in OUTPUT_SCHEMA_TOKEN_PATTERN.finditer(schema):
            token = match.group(1).strip()
            if token and token not in seen:
                tokens.append(token)
                seen.add(token)
        return tokens

    def _ensure_unique_output_basename(self, basename: str, used_output_basenames: dict[str, int]) -> str:
        current_count = used_output_basenames.get(basename, 0) + 1
        used_output_basenames[basename] = current_count
        if current_count == 1:
            return basename
        return f"{basename}_{current_count}"

    def _row_value(self, row: pd.Series, column_lookup: dict[str, str], logical_name: str) -> str:
        actual_column = column_lookup.get(normalize_column_name(logical_name))
        if not actual_column:
            return ""
        value = row.get(actual_column)
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()

    def _first_row_value(
        self,
        row: pd.Series,
        column_lookup: dict[str, str],
        aliases: tuple[str, ...] | list[str],
    ) -> str:
        for alias in aliases:
            actual_column = column_lookup.get(alias)
            if not actual_column:
                continue
            value = row.get(actual_column)
            if pd.isna(value) or value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return ""

    def _sanitize_filename_fragment(self, value: str) -> str:
        sanitized = re.sub(r"[^\w.-]+", "_", value.strip(), flags=re.ASCII)
        sanitized = sanitized.strip("._")
        return sanitized

    def _sanitize_output_basename(self, value: str) -> str:
        sanitized = self._sanitize_filename_fragment(value)
        sanitized = re.sub(r"_+", "_", sanitized)
        return sanitized.strip("._")

    def _resolve_log_path(self, session: ProjectSession) -> Path:
        base_dir = Path(session.output_dir).resolve() if session.output_dir else AppPaths.logs_dir()
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / "generation.log"

    def _validate_output_dir(self, output_dir: str) -> str | None:
        target = Path(output_dir).expanduser()
        if target.exists():
            if not target.is_dir():
                return f"{target} is not a directory"
            if not os.access(target, os.W_OK):
                return f"permission denied for {target}"
            return None

        parent = target.parent if str(target.parent) not in ("", ".") else Path.cwd()
        existing_parent = parent
        while not existing_parent.exists() and existing_parent != existing_parent.parent:
            existing_parent = existing_parent.parent

        if not existing_parent.exists():
            return f"parent directory does not exist for {target}"
        if not os.access(existing_parent, os.W_OK):
            return f"permission denied for {existing_parent}"
        return None

    def _initialize_log(self, log_path: Path):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(log_path, "w", encoding="utf-8") as handle:
            handle.write(f"Document Mapper\nStarted: {timestamp}\n")
            handle.write("=" * 70 + "\n")

    def _write_log(
        self,
        log_path: Path,
        message: str,
        progress_callback: LogCallback | None = None,
    ):
        Logger.info(message, tag="DocumentGenerator")
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write(message + "\n")
        if progress_callback:
            progress_callback(message)

    def _clean_docx_content(self, docx_path: Path) -> bool:
        patterns = (
            "Evaluation Warning: The document was created with Spire.Doc for Python.",
            "Evaluation Warning: The document was created with Spire.Doc for .NET.",
            "Created with Spire.Doc",
            "Spire.Doc Evaluation",
        )
        temp_path = Path(str(docx_path) + ".temp")
        try:
            with zipfile.ZipFile(docx_path, "r") as source_zip:
                with zipfile.ZipFile(temp_path, "w") as target_zip:
                    for info in source_zip.infolist():
                        content = source_zip.read(info.filename)
                        if info.filename.endswith((".xml", ".rels")):
                            try:
                                text = content.decode("utf-8")
                            except UnicodeDecodeError:
                                text = None
                            if text is not None:
                                for pattern in patterns:
                                    text = text.replace(pattern, "")
                                content = text.encode("utf-8")
                        target_zip.writestr(info, content)
            os.replace(temp_path, docx_path)
            return True
        finally:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)

    def _batch_convert_docx_to_pdf(
        self,
        docx_files: list[str],
        output_dir: Path,
        timeout_seconds: int,
        log_path: Path,
        progress_callback: LogCallback | None = None,
    ) -> list[str]:
        if not docx_files:
            return []

        try:
            self.process_runner(
                [
                    "soffice",
                    "--headless",
                    "--nologo",
                    "--nodefault",
                    "--norestore",
                    "--nolockcheck",
                    "--invisible",
                    "--nofirststartwizard",
                    "--convert-to",
                    "pdf:writer_pdf_Export",
                    "--outdir",
                    str(output_dir),
                    *docx_files,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=timeout_seconds,
            )
        except Exception as exc:
            self._write_log(log_path, f"ERROR | PDF conversion failed: {exc}", progress_callback)
            return []

        generated_pdfs: list[str] = []
        for docx_file in docx_files:
            pdf_path = output_dir / (Path(docx_file).stem + ".pdf")
            if pdf_path.exists():
                generated_pdfs.append(str(pdf_path))
                self._write_log(log_path, f"SUCCESS | Created PDF {pdf_path.name}", progress_callback)
            else:
                self._write_log(log_path, f"ERROR | Missing PDF for {Path(docx_file).name}", progress_callback)
        return generated_pdfs

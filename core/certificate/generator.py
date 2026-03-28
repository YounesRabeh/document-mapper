from __future__ import annotations

import os
import re
import subprocess
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Callable

import pandas as pd

from core.certificate.excel_service import ExcelDataService, normalize_column_name
from core.certificate.models import GenerationResult, MappingEntry, ProjectSession
from core.util.logger import Logger

LogCallback = Callable[[str], None]


class CertificateGenerator:
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
            errors.append("Select a Word certificate template.")
        elif not Path(session.template_path).exists():
            errors.append(f"Template file not found: {session.template_path}")

        if not session.output_dir:
            errors.append("Choose an output folder.")
        else:
            try:
                Path(session.output_dir).mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                errors.append(f"Output folder is not writable: {exc}")

        if session.license_path and not Path(session.license_path).exists():
            errors.append(f"License file not found: {session.license_path}")

        if not session.mappings:
            errors.append("Add at least one placeholder mapping.")

        if errors:
            return errors

        try:
            preview = self.excel_service.inspect(session.excel_path)
        except Exception as exc:
            return [f"Cannot read Excel workbook: {exc}"]

        return self.excel_service.validate_mappings(preview.columns, session.mappings)

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
        last_certificate_number: str | None = None

        document_cls, file_format = self._load_spire_dependencies()
        licensed = self._activate_license(document_cls, session.license_path, log_path, progress_callback)

        for index, row in dataframe.iterrows():
            try:
                output_path = self._build_docx_output_path(session, row, index, docx_dir, column_lookup)
                replacements = self._build_replacements(row, session.mappings, column_lookup)
                participant_name = self._participant_name(row, column_lookup, index)

                self._write_log(
                    log_path,
                    f"PROCESS | Generating certificate for {participant_name} ({index + 1}/{total_rows})",
                    progress_callback,
                )

                if normalize_column_name("NUMERO-ATTESTATO") in column_lookup:
                    last_value = row.get(column_lookup[normalize_column_name("NUMERO-ATTESTATO")])
                    if not pd.isna(last_value):
                        last_certificate_number = str(last_value)

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

        if last_certificate_number is not None:
            self._write_log(
                log_path,
                f"INFO | Last certificate number seen: {last_certificate_number}",
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
            last_certificate_number=last_certificate_number,
            log_path=str(log_path),
            errors=generation_errors,
        )

    def _load_spire_dependencies(self):
        try:
            from spire.doc import Document, FileFormat
        except ImportError as exc:
            raise RuntimeError(
                "Spire.Doc is not installed. Install the runtime dependency before generating certificates."
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
        if normalized == "DATA":
            return self._format_date_to_dd_mm_yyyy(value)
        if normalized in {"NOME", "COGNOME"}:
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
        first_name = self._row_value(row, column_lookup, "NOME").upper()
        last_name = self._row_value(row, column_lookup, "COGNOME").upper()
        full_name = " ".join(part for part in (first_name, last_name) if part).strip()
        return full_name or f"row-{row_index + 1}"

    def _build_docx_output_path(
        self,
        session: ProjectSession,
        row: pd.Series,
        row_index: int,
        output_dir: Path,
        column_lookup: dict[str, str],
    ) -> Path:
        first_name = self._sanitize_filename_fragment(self._row_value(row, column_lookup, "NOME").upper())
        last_name = self._sanitize_filename_fragment(self._row_value(row, column_lookup, "COGNOME").upper())
        if not first_name and not last_name:
            fallback = self._sanitize_filename_fragment(f"row_{row_index + 1:03d}")
            first_name = fallback

        parts = [part for part in (first_name, last_name, "attestato", session.certificate_type) if part]
        if session.category.strip():
            parts.append(self._sanitize_filename_fragment(session.category))
        filename = "_".join(parts) + ".docx"
        return output_dir / filename

    def _row_value(self, row: pd.Series, column_lookup: dict[str, str], logical_name: str) -> str:
        actual_column = column_lookup.get(normalize_column_name(logical_name))
        if not actual_column:
            return ""
        value = row.get(actual_column)
        if pd.isna(value) or value is None:
            return ""
        return str(value).strip()

    def _sanitize_filename_fragment(self, value: str) -> str:
        sanitized = re.sub(r"[^\w.-]+", "_", value.strip(), flags=re.ASCII)
        sanitized = sanitized.strip("._")
        return sanitized

    def _resolve_log_path(self, session: ProjectSession) -> Path:
        base_dir = Path(session.output_dir).resolve() if session.output_dir else Path.cwd()
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / "certificate_generation.log"

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
        Logger.info(message, tag="CertificateGenerator")
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

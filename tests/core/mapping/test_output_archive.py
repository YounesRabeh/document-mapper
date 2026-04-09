from __future__ import annotations

from pathlib import Path
import zipfile

import pytest

from core.mapping.models import GenerationResult
from core.mapping.output_archive import (
    ARCHIVE_FORMAT_FOLDER,
    ARCHIVE_FORMAT_ZIP,
    ArchiveCreationError,
    OutputArchiveService,
)


def _build_result_with_outputs(tmp_path: Path) -> GenerationResult:
    docx_dir = tmp_path / "out" / "docx"
    pdf_dir = tmp_path / "out" / "pdf"
    docx_dir.mkdir(parents=True, exist_ok=True)
    pdf_dir.mkdir(parents=True, exist_ok=True)

    docx_path = docx_dir / "ADA_LOVELACE.docx"
    pdf_path = pdf_dir / "ADA_LOVELACE.pdf"
    docx_path.write_text("docx", encoding="utf-8")
    pdf_path.write_text("pdf", encoding="utf-8")

    return GenerationResult(
        total_rows=1,
        success_count=1,
        generated_docx_paths=[str(docx_path)],
        generated_pdf_paths=[str(pdf_path)],
        log_path="",
        errors=[],
    )


def test_available_formats_include_folder_and_zip():
    service = OutputArchiveService()

    assert service.available_formats() == [ARCHIVE_FORMAT_FOLDER, ARCHIVE_FORMAT_ZIP]


def test_create_folder_archive_preserves_docx_and_pdf_sections(tmp_path):
    service = OutputArchiveService()
    result = _build_result_with_outputs(tmp_path)

    archive_path = service.create_archive(result, tmp_path / "archives", "Run 01", ARCHIVE_FORMAT_FOLDER)

    assert archive_path.name == "Run_01"
    assert archive_path.is_dir()
    assert (archive_path / "docx" / "ADA_LOVELACE.docx").exists()
    assert (archive_path / "pdf" / "ADA_LOVELACE.pdf").exists()


def test_create_zip_archive_preserves_docx_and_pdf_sections(tmp_path):
    service = OutputArchiveService()
    result = _build_result_with_outputs(tmp_path)

    archive_path = service.create_archive(result, tmp_path / "archives", "Run 01", ARCHIVE_FORMAT_ZIP)

    assert archive_path.name == "Run_01.zip"
    assert archive_path.exists()
    with zipfile.ZipFile(archive_path, "r") as archive:
        names = sorted(archive.namelist())
    assert names == ["docx/ADA_LOVELACE.docx", "pdf/ADA_LOVELACE.pdf"]


def test_create_archive_rejects_results_with_errors(tmp_path):
    service = OutputArchiveService()
    result = _build_result_with_outputs(tmp_path)
    result.errors = ["Failed to generate row 1."]

    with pytest.raises(ArchiveCreationError) as raised:
        service.create_archive(result, tmp_path / "archives", "Run 01", ARCHIVE_FORMAT_ZIP)

    assert raised.value.code == "has_errors"


def test_create_archive_rejects_empty_file_lists(tmp_path):
    service = OutputArchiveService()
    result = GenerationResult(total_rows=1, success_count=0, generated_docx_paths=[], generated_pdf_paths=[], errors=[])

    with pytest.raises(ArchiveCreationError) as raised:
        service.create_archive(result, tmp_path / "archives", "Run 01", ARCHIVE_FORMAT_ZIP)

    assert raised.value.code == "no_files"


def test_create_archive_respects_overwrite_flag(tmp_path):
    service = OutputArchiveService()
    result = _build_result_with_outputs(tmp_path)
    archive_root = tmp_path / "archives"

    first_archive = service.create_archive(result, archive_root, "Run 01", ARCHIVE_FORMAT_FOLDER)
    assert first_archive.exists()

    with pytest.raises(ArchiveCreationError) as raised:
        service.create_archive(result, archive_root, "Run 01", ARCHIVE_FORMAT_FOLDER)
    assert raised.value.code == "already_exists"

    overwrite_archive = service.create_archive(
        result,
        archive_root,
        "Run 01",
        ARCHIVE_FORMAT_FOLDER,
        overwrite=True,
    )
    assert overwrite_archive == first_archive
    assert overwrite_archive.exists()


def test_create_archive_normalizes_run_name_for_filename(tmp_path):
    service = OutputArchiveService()
    result = _build_result_with_outputs(tmp_path)

    archive_path = service.create_archive(
        result,
        tmp_path / "archives",
        "  Batch: Ada / Lovelace 2026.zip  ",
        ARCHIVE_FORMAT_ZIP,
    )

    assert archive_path.name == "Batch_Ada_Lovelace_2026.zip"


def test_create_archive_rejects_invalid_run_name(tmp_path):
    service = OutputArchiveService()
    result = _build_result_with_outputs(tmp_path)

    with pytest.raises(ArchiveCreationError) as raised:
        service.create_archive(result, tmp_path / "archives", " . . ", ARCHIVE_FORMAT_ZIP)

    assert raised.value.code == "invalid_run_name"

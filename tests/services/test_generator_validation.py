from __future__ import annotations

import pandas as pd

from core.certificate.generator import CertificateGenerator
from core.certificate.models import MappingEntry, ProjectSession
from tests.helpers.fakes import FakeExcelService


def test_validate_session_reports_missing_columns(tmp_path):
    generator = CertificateGenerator(excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada"}])))
    template_path = tmp_path / "template.docx"
    excel_path = tmp_path / "data.xlsx"
    template_path.write_text("template", encoding="utf-8")
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        detected_placeholder_delimiter="<<",
        detected_placeholder_count=1,
        mappings=[MappingEntry(placeholder="<<COGNOME>>", column_name="COGNOME")],
    )

    errors = generator.validate_session(session)

    assert any("COGNOME" in error for error in errors)


def test_validate_session_requires_output_naming_schema(tmp_path):
    generator = CertificateGenerator(
        excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}]))
    )
    template_path = tmp_path / "template.docx"
    excel_path = tmp_path / "data.xlsx"
    template_path.write_text("template", encoding="utf-8")
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        detected_placeholder_delimiter="<<",
        detected_placeholder_count=1,
        output_naming_schema="",
        mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
    )

    errors = generator.validate_session(session)

    assert "Set an output naming schema before continuing." in errors


def test_validate_session_reports_unknown_output_naming_schema_token(tmp_path):
    generator = CertificateGenerator(
        excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}]))
    )
    template_path = tmp_path / "template.docx"
    excel_path = tmp_path / "data.xlsx"
    template_path.write_text("template", encoding="utf-8")
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        detected_placeholder_delimiter="<<",
        detected_placeholder_count=1,
        output_naming_schema="{UNKNOWN}_{NOME}",
        mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
    )

    errors = generator.validate_session(session)

    assert "Output naming schema token 'UNKNOWN' is not available as a workbook column or built-in value." in errors


def test_validate_session_requires_placeholder_delimiter(tmp_path):
    generator = CertificateGenerator(excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada"}])))
    template_path = tmp_path / "template.docx"
    excel_path = tmp_path / "data.xlsx"
    template_path.write_text("template", encoding="utf-8")
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
    )
    session.placeholder_delimiter = ""

    errors = generator.validate_session(session)

    assert "Set a placeholder delimiter before continuing." in errors


def test_validate_session_requires_placeholder_detection_for_current_delimiter(tmp_path):
    generator = CertificateGenerator(excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada"}])))
    template_path = tmp_path / "template.docx"
    excel_path = tmp_path / "data.xlsx"
    template_path.write_text("template", encoding="utf-8")
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        placeholder_delimiter="<<",
        mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
    )

    errors = generator.validate_session(session)

    assert "Refresh and detect at least one placeholder before continuing." in errors

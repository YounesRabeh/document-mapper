from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd

from core.certificate.generator import CertificateGenerator
from core.certificate.models import MappingEntry, ProjectSession
from core.util.app_paths import AppPaths
from tests.helpers.fakes import FakeExcelService, fake_spire_dependencies


def test_generator_uses_app_logs_dir_when_output_dir_missing(tmp_path):
    generator = CertificateGenerator(excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada"}])))

    with patch.object(AppPaths, "logs_dir", return_value=tmp_path):
        log_path = generator._resolve_log_path(ProjectSession(output_dir=""))

    assert log_path == tmp_path / "certificate_generation.log"


def test_generator_formats_dates_and_creates_docx(tmp_path):
    dataframe = pd.DataFrame(
        [
            {
                "NOME": "Ada",
                "COGNOME": "Lovelace",
                "DATA": pd.Timestamp("2026-03-28"),
                "NUMERO-ATTESTATO": "42A",
            }
        ]
    )
    excel_service = FakeExcelService(dataframe)
    generator = CertificateGenerator(excel_service=excel_service)
    generator._load_spire_dependencies = fake_spire_dependencies  # type: ignore[method-assign]
    generator._clean_docx_content = lambda _path: True  # type: ignore[method-assign]

    template_path = tmp_path / "template.docx"
    template_path.write_text("template", encoding="utf-8")
    excel_path = tmp_path / "data.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        output_naming_schema="{NOME}_{COGNOME}_{TEMPLATE}",
        placeholder_delimiter="<<",
        detected_placeholder_delimiter="<<",
        detected_placeholder_count=2,
        mappings=[
            MappingEntry(placeholder="<<NOME>>", column_name="NOME"),
            MappingEntry(placeholder="<<DATA>>", column_name="DATA"),
        ],
    )

    result = generator.generate(session)

    assert result.success_count == 1
    assert result.last_certificate_number == "42A"
    assert len(result.generated_docx_paths) == 1
    assert Path(result.generated_docx_paths[0]).exists()


def test_generator_supports_english_field_aliases_for_dates_names_and_certificate_numbers(tmp_path):
    dataframe = pd.DataFrame(
        [
            {
                "NAME": "Ada",
                "LASTNAME": "Lovelace",
                "COURSE_DATE": pd.Timestamp("2026-03-28"),
                "CERTIFICATE_NO": "A7K9M2Q4R8T1",
            }
        ]
    )
    excel_service = FakeExcelService(dataframe)
    generator = CertificateGenerator(excel_service=excel_service)
    generator._load_spire_dependencies = fake_spire_dependencies  # type: ignore[method-assign]
    generator._clean_docx_content = lambda _path: True  # type: ignore[method-assign]

    template_path = tmp_path / "template.docx"
    template_path.write_text("template", encoding="utf-8")
    excel_path = tmp_path / "data.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        output_naming_schema="{NAME}_{LASTNAME}_{TEMPLATE}",
        placeholder_delimiter="<",
        detected_placeholder_delimiter="<",
        detected_placeholder_count=2,
        mappings=[
            MappingEntry(placeholder="<NAME>", column_name="NAME"),
            MappingEntry(placeholder="<COURSE_DATE>", column_name="COURSE_DATE"),
        ],
    )

    result = generator.generate(session)
    column_lookup = excel_service.build_column_lookup([str(column) for column in dataframe.columns])
    participant_name = generator._participant_name(dataframe.iloc[0], column_lookup, 0)
    replacements = generator._build_replacements(dataframe.iloc[0], session.mappings, column_lookup)

    assert result.success_count == 1
    assert result.last_certificate_number == "A7K9M2Q4R8T1"
    assert participant_name == "ADA LOVELACE"
    assert replacements["<NAME>"] == "ADA"
    assert replacements["<COURSE_DATE>"] == "28/03/2026"


def test_generator_creates_pdfs_when_enabled(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])

    def fake_runner(command, **_kwargs):
        output_index = command.index("--outdir") + 1
        output_dir = Path(command[output_index])
        for docx_file in command[output_index + 1 :]:
            (output_dir / f"{Path(docx_file).stem}.pdf").write_text("pdf", encoding="utf-8")
        return SimpleNamespace(returncode=0)

    generator = CertificateGenerator(excel_service=FakeExcelService(dataframe), process_runner=fake_runner)
    generator._load_spire_dependencies = fake_spire_dependencies  # type: ignore[method-assign]
    generator._clean_docx_content = lambda _path: True  # type: ignore[method-assign]

    template_path = tmp_path / "template.docx"
    template_path.write_text("template", encoding="utf-8")
    excel_path = tmp_path / "data.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        output_naming_schema="{NOME}_{COGNOME}_{TEMPLATE}",
        placeholder_delimiter="<<",
        detected_placeholder_delimiter="<<",
        detected_placeholder_count=1,
        export_pdf=True,
        mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
    )

    result = generator.generate(session)

    assert result.success_count == 1
    assert len(result.generated_pdf_paths) == 1
    assert Path(result.generated_pdf_paths[0]).exists()

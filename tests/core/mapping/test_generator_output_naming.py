from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.mapping.generator import DocumentGenerator
from core.mapping.models import ProjectSession
from tests.helpers.fakes import FakeExcelService


def test_generator_sanitizes_template_name_filename_fragment(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = DocumentGenerator(excel_service=FakeExcelService(dataframe))
    template_path = tmp_path / "MODELLO ATTESTATO integrale PS 12 ORE tipo B e C.docx"

    output_path = generator._build_docx_output_path(
        ProjectSession(
            output_dir=str(tmp_path),
            template_path=str(template_path),
            output_naming_schema="{NOME}_{COGNOME}_{TEMPLATE}",
        ),
        dataframe.iloc[0],
        0,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
    )

    assert output_path.name == "ADA_LOVELACE_MODELLO_ATTESTATO_integrale_PS_12_ORE_tipo_B_e_C.docx"


def test_generator_resolves_output_naming_schema_tokens(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = DocumentGenerator(excel_service=FakeExcelService(dataframe))
    template_path = tmp_path / "MODELLO ATTESTATO integrale PS 12 ORE tipo B e C.docx"

    output_path = generator._build_docx_output_path(
        ProjectSession(
            output_dir=str(tmp_path),
            template_path=str(template_path),
            output_naming_schema="{COGNOME}_{NOME}_{ROW}_{TEMPLATE}",
        ),
        dataframe.iloc[0],
        0,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
    )

    assert output_path.name == "LOVELACE_ADA_1_MODELLO_ATTESTATO_integrale_PS_12_ORE_tipo_B_e_C.docx"


def test_generator_falls_back_to_row_name_when_schema_resolves_empty(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = DocumentGenerator(excel_service=FakeExcelService(dataframe))

    output_path = generator._build_docx_output_path(
        ProjectSession(
            output_dir=str(tmp_path),
            output_naming_schema="///",
        ),
        dataframe.iloc[0],
        0,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
    )

    assert output_path.name == "row_001.docx"


def test_generator_appends_counter_for_duplicate_output_names(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = DocumentGenerator(excel_service=FakeExcelService(dataframe))
    used_output_basenames: dict[str, int] = {}
    session = ProjectSession(
        output_dir=str(tmp_path),
        output_naming_schema="{NOME}",
    )

    first_path = generator._build_docx_output_path(
        session,
        dataframe.iloc[0],
        0,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
        used_output_basenames,
    )
    second_path = generator._build_docx_output_path(
        session,
        dataframe.iloc[0],
        1,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
        used_output_basenames,
    )

    assert first_path.name == "ADA.docx"
    assert second_path.name == "ADA_2.docx"


def test_existing_output_conflicts_detects_docx_and_pdf_targets(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = DocumentGenerator(excel_service=FakeExcelService(dataframe))
    template_path = tmp_path / "template.docx"
    template_path.write_text("template", encoding="utf-8")
    excel_path = tmp_path / "data.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")

    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        output_naming_schema="{NOME}_{COGNOME}_{TEMPLATE}",
        export_pdf=True,
    )

    docx_path = tmp_path / "docx" / "ADA_LOVELACE_template.docx"
    pdf_path = tmp_path / "pdf" / "ADA_LOVELACE_template.pdf"
    docx_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    docx_path.write_text("existing", encoding="utf-8")
    pdf_path.write_text("existing", encoding="utf-8")

    conflicts = generator.existing_output_conflicts(session)

    assert conflicts == [str(docx_path), str(pdf_path)]


def test_existing_output_conflicts_returns_empty_when_targets_do_not_exist(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = DocumentGenerator(excel_service=FakeExcelService(dataframe))
    template_path = tmp_path / "template.docx"
    template_path.write_text("template", encoding="utf-8")
    excel_path = tmp_path / "data.xlsx"
    excel_path.write_text("placeholder", encoding="utf-8")
    session = ProjectSession(
        excel_path=str(excel_path),
        template_path=str(template_path),
        output_dir=str(tmp_path),
        output_naming_schema="{NOME}_{COGNOME}_{TEMPLATE}",
        export_pdf=True,
    )

    assert generator.existing_output_conflicts(session) == []

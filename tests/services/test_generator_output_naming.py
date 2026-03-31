from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.certificate.generator import CertificateGenerator
from core.certificate.models import ProjectSession
from tests.helpers.fakes import FakeExcelService


def test_generator_sanitizes_certificate_type_filename_fragment(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = CertificateGenerator(excel_service=FakeExcelService(dataframe))

    output_path = generator._build_docx_output_path(
        ProjectSession(
            output_dir=str(tmp_path),
            certificate_type="MODELLO ATTESTATO integrale PS 12 ORE tipo B e C",
        ),
        dataframe.iloc[0],
        0,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
    )

    assert output_path.name == "ADA_LOVELACE_attestato_MODELLO_ATTESTATO_integrale_PS_12_ORE_tipo_B_e_C.docx"


def test_generator_resolves_output_naming_schema_tokens(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = CertificateGenerator(excel_service=FakeExcelService(dataframe))

    output_path = generator._build_docx_output_path(
        ProjectSession(
            output_dir=str(tmp_path),
            certificate_type="MODELLO ATTESTATO integrale PS 12 ORE tipo B e C",
            output_naming_schema="{COGNOME}_{NOME}_{ROW}_{CERTIFICATE_TYPE}",
        ),
        dataframe.iloc[0],
        0,
        Path(tmp_path),
        {"NOME": "NOME", "COGNOME": "COGNOME"},
    )

    assert output_path.name == "LOVELACE_ADA_1_MODELLO_ATTESTATO_integrale_PS_12_ORE_tipo_B_e_C.docx"


def test_generator_falls_back_to_row_name_when_schema_resolves_empty(tmp_path):
    dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])
    generator = CertificateGenerator(excel_service=FakeExcelService(dataframe))

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
    generator = CertificateGenerator(excel_service=FakeExcelService(dataframe))
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

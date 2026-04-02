from __future__ import annotations

from core.certificate.models import (
    DEFAULT_OUTPUT_NAMING_SCHEMA,
    DEFAULT_PLACEHOLDER_DELIMITER,
    ProjectSession,
    normalize_certificate_type,
)


def test_normalize_certificate_type_strips_template_extension():
    assert (
        normalize_certificate_type("MODELLO ATTESTATO integrale PS 12 ORE tipo B e C.docx")
        == "MODELLO ATTESTATO integrale PS 12 ORE tipo B e C"
    )


def test_project_session_defaults_placeholder_delimiter_and_output_schema():
    session = ProjectSession()

    assert session.output_naming_schema == DEFAULT_OUTPUT_NAMING_SCHEMA
    assert session.placeholder_delimiter == DEFAULT_PLACEHOLDER_DELIMITER
    assert session.placeholder_start == "<"
    assert session.placeholder_end == ">"


def test_project_session_infers_placeholder_delimiter_from_legacy_mappings():
    session = ProjectSession.from_dict(
        {
            "mappings": [
                {"placeholder": "<NOME>", "column_name": "NOME"},
            ]
        }
    )

    assert session.placeholder_delimiter == "<"
    assert session.placeholder_start == "<"
    assert session.placeholder_end == ">"

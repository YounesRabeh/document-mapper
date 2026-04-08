from __future__ import annotations

import zipfile
from unittest.mock import patch

import pytest

from core.mapping.template_service import TemplatePlaceholderService


def test_extracts_placeholders_from_docx(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.docx"
    with zipfile.ZipFile(template_path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p>"
                "<w:r><w:t>Hello </w:t></w:r>"
                "<w:r><w:t>&lt;&lt;NOME&gt;&gt;</w:t></w:r>"
                "<w:r><w:t> and </w:t></w:r>"
                "<w:r><w:t>&lt;DATA&gt;</w:t></w:r>"
                "</w:p></w:body></w:document>"
            ),
        )

    placeholders = service.extract_placeholders(str(template_path), "<<")

    assert placeholders == ["<<NOME>>"]


def test_extracts_doc_placeholders_through_spire_backend(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.doc"
    template_path.write_text("placeholder", encoding="utf-8")

    with patch.object(service, "_spire_is_available", return_value=True), patch.object(
        service,
        "_extract_doc_text_with_spire",
        return_value="Hello %NOME% and %DATA%",
    ) as extract_spire:
        placeholders = service.extract_placeholders(str(template_path), "%")

    assert placeholders == ["%NOME%", "%DATA%"]
    extract_spire.assert_called_once()


def test_extracts_doc_placeholders_through_soffice_when_spire_is_unavailable(tmp_path):
    service = TemplatePlaceholderService(soffice_resolver=lambda _name: "/usr/bin/soffice")
    template_path = tmp_path / "template.doc"
    template_path.write_text("placeholder", encoding="utf-8")

    with patch.object(service, "_spire_is_available", return_value=False), patch.object(
        service,
        "_extract_doc_text_with_soffice",
        return_value="Hello %NOME% and %DATA%",
    ) as extract_soffice:
        placeholders = service.extract_placeholders(str(template_path), "%")

    assert placeholders == ["%NOME%", "%DATA%"]
    extract_soffice.assert_called_once_with(template_path.resolve(), "/usr/bin/soffice")


def test_doc_placeholder_detection_falls_back_to_soffice_when_spire_extract_fails(tmp_path):
    service = TemplatePlaceholderService(soffice_resolver=lambda _name: "/usr/bin/soffice")
    template_path = tmp_path / "template.doc"
    template_path.write_text("placeholder", encoding="utf-8")

    with patch.object(service, "_spire_is_available", return_value=True), patch.object(
        service,
        "_extract_doc_text_with_spire",
        side_effect=RuntimeError("spire failed"),
    ), patch.object(
        service,
        "_extract_doc_text_with_soffice",
        return_value="Hello %NOME% and %DATA%",
    ) as extract_soffice:
        placeholders = service.extract_placeholders(str(template_path), "%")

    assert placeholders == ["%NOME%", "%DATA%"]
    extract_soffice.assert_called_once_with(template_path.resolve(), "/usr/bin/soffice")


def test_doc_placeholder_detection_requires_real_backend(tmp_path):
    service = TemplatePlaceholderService(soffice_resolver=lambda _name: None)
    template_path = tmp_path / "template.doc"
    template_path.write_text("placeholder", encoding="utf-8")

    with patch.object(service, "_spire_is_available", return_value=False), pytest.raises(RuntimeError) as exc:
        service.extract_placeholders(str(template_path), "%")

    assert "Spire.Doc or LibreOffice" in str(exc.value)


def test_does_not_match_nested_double_delimiters_as_single(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.docx"
    with zipfile.ZipFile(template_path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Hello &lt;&lt;NOME&gt;&gt; only</w:t></w:r></w:p></w:body></w:document>"
            ),
        )

    placeholders = service.extract_placeholders(str(template_path), "<")

    assert placeholders == []


def test_returns_no_matches_for_empty_delimiters(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.docx"
    with zipfile.ZipFile(template_path, "w") as archive:
        archive.writestr(
            "word/document.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
                "<w:body><w:p><w:r><w:t>Hello &lt;&lt;NOME&gt;&gt;</w:t></w:r></w:p></w:body></w:document>"
            ),
        )

    placeholders = service.extract_placeholders(str(template_path), "")

    assert placeholders == []


def test_cache_is_backend_aware_until_cleared(tmp_path):
    class CountingTemplateService(TemplatePlaceholderService):
        def __init__(self):
            super().__init__()
            self.extract_calls = 0
            self.backend_id = "spire_doc"

        def _detect_backend(self, _path):
            return self.backend_id

        def _extract_template_text(self, _path, _backend_id=None):
            self.extract_calls += 1
            return "Hello <<NOME>>"

    service = CountingTemplateService()
    template_path = tmp_path / "template.doc"
    template_path.write_text("placeholder", encoding="utf-8")

    placeholders_one = service.extract_placeholders(str(template_path), "<<")
    placeholders_two = service.extract_placeholders(str(template_path), "<<")
    service.backend_id = "soffice_doc:/usr/bin/soffice"
    placeholders_three = service.extract_placeholders(str(template_path), "<<")
    service.clear_cache(str(template_path))
    placeholders_four = service.extract_placeholders(str(template_path), "<<")

    assert placeholders_one == ["<<NOME>>"]
    assert placeholders_two == ["<<NOME>>"]
    assert placeholders_three == ["<<NOME>>"]
    assert placeholders_four == ["<<NOME>>"]
    assert service.extract_calls == 3

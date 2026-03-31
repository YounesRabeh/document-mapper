from __future__ import annotations

import zipfile

from core.certificate.template_service import TemplatePlaceholderService


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


def test_extracts_placeholders_with_custom_delimiters(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.doc"
    template_path.write_text("Hello %NOME% and %DATA%", encoding="utf-8")

    placeholders = service.extract_placeholders(str(template_path), "%")

    assert placeholders == ["%NOME%", "%DATA%"]


def test_does_not_match_nested_double_delimiters_as_single(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.doc"
    template_path.write_text("Hello <<NOME>> only", encoding="utf-8")

    placeholders = service.extract_placeholders(str(template_path), "<")

    assert placeholders == []


def test_returns_no_matches_for_empty_delimiters(tmp_path):
    service = TemplatePlaceholderService()
    template_path = tmp_path / "template.doc"
    template_path.write_text("Hello <<NOME>>", encoding="utf-8")

    placeholders = service.extract_placeholders(str(template_path), "")

    assert placeholders == []


def test_uses_cache_until_cleared(tmp_path):
    class CountingTemplateService(TemplatePlaceholderService):
        def __init__(self):
            super().__init__()
            self.extract_calls = 0

        def _extract_template_text(self, path):
            self.extract_calls += 1
            return super()._extract_binary_text(path)

    service = CountingTemplateService()
    template_path = tmp_path / "template.doc"
    template_path.write_text("Hello <<NOME>>", encoding="utf-8")

    placeholders_one = service.extract_placeholders(str(template_path), "<<")
    placeholders_two = service.extract_placeholders(str(template_path), "<<")
    service.clear_cache(str(template_path))
    placeholders_three = service.extract_placeholders(str(template_path), "<<")

    assert placeholders_one == ["<<NOME>>"]
    assert placeholders_two == ["<<NOME>>"]
    assert placeholders_three == ["<<NOME>>"]
    assert service.extract_calls == 2

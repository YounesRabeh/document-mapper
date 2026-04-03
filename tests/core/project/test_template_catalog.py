from __future__ import annotations

from pathlib import Path

from core.certificate.models import ProjectSession, ProjectTemplateEntry, ProjectTemplateType
from core.project import TemplateCatalogService


def test_seed_default_template_populates_empty_catalog(tmp_path):
    default_template = tmp_path / "default_template_01.docx"
    default_template.write_text("template", encoding="utf-8")
    session = ProjectSession()

    service = TemplateCatalogService(lambda: default_template)
    service.seed_default_template(session)

    assert [entry.name for entry in session.template_types] == ["Default template"]
    assert len(session.templates) == 1
    assert session.templates[0].label == "Default template 01"
    assert session.selected_template_type == "Default template"
    assert session.selected_template == session.templates[0].id
    assert session.template_path == str(default_template)


def test_build_unsaved_copy_detaches_managed_templates_from_project_dir(tmp_path):
    project_dir = tmp_path / "project"
    templates_dir = project_dir / "templates"
    templates_dir.mkdir(parents=True)
    managed_template = templates_dir / "invoice.docx"
    managed_template.write_text("managed", encoding="utf-8")

    entry = ProjectTemplateEntry(
        display_name="Invoice 01",
        type_name="Invoices",
        relative_path="templates/invoice.docx",
        source_path="",
        is_managed=True,
    )
    session = ProjectSession(
        template_types=[ProjectTemplateType("Invoices")],
        templates=[entry],
        selected_template_type="Invoices",
        selected_template=entry.id,
        template_path=str(managed_template),
    )

    copied = TemplateCatalogService(lambda: None).build_unsaved_copy(session, project_dir)

    assert copied.template_path == ""
    assert copied.templates[0].is_managed is False
    assert copied.templates[0].relative_path == ""
    assert copied.templates[0].source_path == str(managed_template.resolve())
    assert session.templates[0].is_managed is True


def test_store_template_override_in_project_creates_selected_entry(tmp_path):
    override_template = tmp_path / "Letter.docx"
    override_template.write_text("override", encoding="utf-8")
    session = ProjectSession(
        selected_template_type="Letters",
        template_types=[ProjectTemplateType("Letters")],
        template_override_path=str(override_template),
    )

    service = TemplateCatalogService(lambda: None)
    service.store_template_override_in_project(session)

    assert session.template_override_path == ""
    assert len(session.templates) == 1
    assert session.templates[0].label == "Letter"
    assert session.selected_template == session.templates[0].id
    assert session.selected_template_type == "Letters"


def test_unique_template_display_name_appends_counter_for_duplicates():
    session = ProjectSession(
        template_types=[ProjectTemplateType("Letters")],
        templates=[
            ProjectTemplateEntry(display_name="Offer", type_name="Letters"),
            ProjectTemplateEntry(display_name="Offer 2", type_name="Letters"),
        ],
    )

    service = TemplateCatalogService(lambda: Path("/tmp/default.docx"))

    assert service.unique_template_display_name(session, "Letters", "Offer") == "Offer 3"

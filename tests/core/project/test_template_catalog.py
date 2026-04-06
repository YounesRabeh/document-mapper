from __future__ import annotations

from core.certificate.models import ProjectSession, ProjectTemplateEntry, ProjectTemplateType
from core.project import TemplateCatalogService


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

    copied = TemplateCatalogService().build_unsaved_copy(session, project_dir)

    assert copied.template_path == ""
    assert copied.templates[0].is_managed is False
    assert copied.templates[0].relative_path == ""
    assert copied.templates[0].source_path == str(managed_template.resolve())
    assert session.templates[0].is_managed is True


def test_infer_project_dir_from_session_uses_selected_managed_template_path(tmp_path):
    project_dir = tmp_path / "project"
    templates_dir = project_dir / "templates"
    templates_dir.mkdir(parents=True)
    managed_template = templates_dir / "invoice.docx"
    managed_template.write_text("managed", encoding="utf-8")

    entry = ProjectTemplateEntry(
        display_name="Invoice 01",
        type_name="Invoices",
        relative_path="templates/invoice.docx",
        is_managed=True,
    )
    session = ProjectSession(
        template_types=[ProjectTemplateType("Invoices")],
        templates=[entry],
        selected_template_type="Invoices",
        selected_template=entry.id,
        template_path=str(managed_template),
    )

    inferred = TemplateCatalogService().infer_project_dir_from_session(session)

    assert inferred == project_dir.resolve()


def test_store_template_override_in_project_creates_selected_entry(tmp_path):
    override_template = tmp_path / "Letter.docx"
    override_template.write_text("override", encoding="utf-8")
    session = ProjectSession(
        selected_template_type="Letters",
        template_types=[ProjectTemplateType("Letters")],
        template_override_path=str(override_template),
    )

    service = TemplateCatalogService()
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

    service = TemplateCatalogService()

    assert service.unique_template_display_name(session, "Letters", "Offer") == "Offer 3"

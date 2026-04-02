from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox

from core.certificate.models import ProjectTemplateEntry, ProjectTemplateType, normalize_template_name


def assert_stage_state(window, stage_index: int, *, active=None, blocked=None, completed=None):
    card = window.stage_cards[stage_index]
    if active is not None:
        assert bool(card.property("active")) is active
    if blocked is not None:
        assert bool(card.property("blocked")) is blocked
    if completed is not None:
        assert bool(card.property("completed")) is completed


def populate_setup_page(window, workbook: Path, template: Path, output_dir: Path):
    window.setup_page.excel_input["input"].setText(str(workbook))
    window.setup_page.output_input["input"].setText(str(output_dir))
    window.setup_page._sync_session()
    template_type = "General"
    template_entry = ProjectTemplateEntry(
        display_name=normalize_template_name(template.name),
        type_name=template_type,
        source_path=str(template),
        is_managed=False,
    )
    window.session.template_types = [ProjectTemplateType(template_type)]
    window.session.templates = [template_entry]
    window.session.selected_template_type = template_type
    window.session.selected_template = template_entry.id
    window.session.template_path = str(template)
    window.session.mappings = []
    window.session.detected_placeholder_delimiter = ""
    window.session.detected_placeholder_count = 0
    window._refresh_pages()


def mapping_combo(window, row: int, column: int) -> QComboBox:
    return window.mapping_page._get_cell_editor(row, column, QComboBox)

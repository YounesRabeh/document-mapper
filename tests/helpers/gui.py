from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QComboBox


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
    window.setup_page.template_input["input"].setText(str(template))
    window.setup_page.output_input["input"].setText(str(output_dir))
    window.setup_page._sync_session()


def mapping_combo(window, row: int, column: int) -> QComboBox:
    return window.mapping_page._get_cell_editor(row, column, QComboBox)

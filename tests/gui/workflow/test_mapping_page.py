from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from core.mapping.models import DEFAULT_OUTPUT_NAMING_SCHEMA
from tests.helpers.gui import assert_stage_state, mapping_combo


def _go_to_mapping(window):
    window.stage_cards[2].clicked.emit(2)
    assert window.stage_manager.currentIndex() == 1


def _add_first_mapping_row(window):
    if window.mapping_page.mapping_table.rowCount() == 0:
        window.mapping_page.add_button.click()
    placeholder_combo = mapping_combo(window, 0, 0)
    placeholder_combo.setCurrentText("<NAME>")
    return placeholder_combo


def _assign_first_mapping(window):
    _add_first_mapping_row(window)
    column_combo = mapping_combo(window, 0, 1)
    column_combo.setCurrentText("NAME")
    window.mapping_page._sync_session_from_table()
    window.mapping_page.refresh_button.click()


def test_mapping_page_tracks_delimiter_detection_and_blocks_generate(prepared_window):
    window = prepared_window.window

    _go_to_mapping(window)

    assert window.mapping_page.mapping_table.rowCount() == 1
    assert mapping_combo(window, 0, 0).currentText() == "<NAME>"
    assert window.session.mappings[0].placeholder == "<NAME>"
    assert window.session.mappings[0].column_name == ""

    _assign_first_mapping(window)
    assert_stage_state(window, 3, blocked=False, completed=False)
    assert window.session.detected_placeholder_delimiter == "<"
    assert window.session.detected_placeholder_count == 1

    window.mapping_page.delimiter_input.setText("{   ")
    QTest.qWait(250)

    assert window.mapping_page.delimiter_input.text() == "{"
    assert window.session.placeholder_delimiter == "{"
    assert window.session.placeholder_start == "{"
    assert window.session.placeholder_end == "}"
    assert window.session.detected_placeholder_delimiter == "{"
    assert window.session.detected_placeholder_count == 0
    assert_stage_state(window, 3, blocked=True)
    assert window.mapping_page.detected_placeholders == []
    assert window.session.mappings == []
    assert window.mapping_page.mapping_table.rowCount() == 0

    window.mapping_page.delimiter_input.clear()
    assert window.session.placeholder_delimiter == ""
    assert_stage_state(window, 3, blocked=True)
    assert hasattr(window.mapping_page, "next_button") is False
    window.stage_cards[3].clicked.emit(3)
    assert window.stage_manager.currentIndex() == 1

    window.mapping_page.delimiter_input.setText("<")
    QTest.qWait(250)

    assert window.session.placeholder_delimiter == "<"
    assert_stage_state(window, 3, blocked=True)
    assert window.mapping_page.mapping_table.rowCount() == 1
    assert mapping_combo(window, 0, 0).currentText() == "<NAME>"
    assert window.session.detected_placeholder_delimiter == "<"
    assert window.session.detected_placeholder_count == 1

    _assign_first_mapping(window)
    assert_stage_state(window, 3, blocked=False)


def test_refresh_reloads_detected_placeholders_into_table(prepared_window):
    window = prepared_window.window

    _go_to_mapping(window)
    assert window.mapping_page.mapping_table.rowCount() == 1

    window.mapping_page.mapping_table.removeRow(0)
    window.mapping_page._sync_session_from_table()
    assert window.mapping_page.mapping_table.rowCount() == 0
    assert window.session.mappings == []

    window.mapping_page.refresh_button.click()

    assert window.mapping_page.mapping_table.rowCount() == 1
    assert mapping_combo(window, 0, 0).currentText() == "<NAME>"
    assert window.session.mappings[0].placeholder == "<NAME>"
    assert window.session.mappings[0].column_name == ""


def test_output_naming_schema_token_insertion_updates_session(prepared_window):
    window = prepared_window.window

    _go_to_mapping(window)
    assert hasattr(window.mapping_page.ui, "leftBox") is False
    _assign_first_mapping(window)

    assert window.mapping_page.delimiter_input.text() == "<"
    assert window.mapping_page.output_naming_schema_input.text() == DEFAULT_OUTPUT_NAMING_SCHEMA
    assert window.mapping_page.output_naming_schema_input.available_tokens() == [
        "NAME",
        "LASTNAME",
        "ROW",
        "TEMPLATE",
    ]

    schema_input = window.mapping_page.output_naming_schema_input
    schema_input.clear()
    assert window.session.output_naming_schema == ""
    assert_stage_state(window, 3, blocked=True)

    schema_input.setFocus()
    QTest.keyClicks(schema_input, "{")
    QTest.qWait(80)
    assert schema_input.token_completer.popup().isVisible()
    schema_input.token_completer.activated[str].emit("NAME")
    assert schema_input.text() == "{NAME}"
    assert schema_input.cursorPosition() == len("{NAME}")

    QTest.keyClicks(schema_input, "(mytext){")
    QTest.qWait(80)
    schema_input.token_completer.activated[str].emit("LASTNAME")
    assert schema_input.text() == "{NAME}(mytext){LASTNAME}"
    assert window.session.output_naming_schema == "{NAME}(mytext){LASTNAME}"
    assert_stage_state(window, 3, blocked=False)

    schema_input.setText(DEFAULT_OUTPUT_NAMING_SCHEMA)
    assert window.session.output_naming_schema == DEFAULT_OUTPUT_NAMING_SCHEMA
    assert_stage_state(window, 3, blocked=False)


def test_mapping_combo_ignores_mouse_wheel_when_popup_is_closed(prepared_window):
    window = prepared_window.window

    _go_to_mapping(window)
    _assign_first_mapping(window)

    column_combo = mapping_combo(window, 0, 1)
    original_text = column_combo.currentText()
    assert original_text == "NAME"

    center = QPointF(column_combo.rect().center())
    global_center = QPointF(column_combo.mapToGlobal(QPoint(int(center.x()), int(center.y()))))
    wheel_event = QWheelEvent(
        center,
        global_center,
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollPhase.ScrollUpdate,
        False,
    )

    QApplication.sendEvent(column_combo, wheel_event)

    assert column_combo.currentText() == original_text

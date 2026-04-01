from __future__ import annotations

from unittest.mock import patch

from PySide6.QtTest import QTest

from core.certificate.models import DEFAULT_OUTPUT_NAMING_SCHEMA
from tests.helpers.gui import assert_stage_state, mapping_combo


def _go_to_mapping(window):
    window.stage_cards[2].clicked.emit(2)
    assert window.stage_manager.currentIndex() == 1


def _assign_first_mapping(window):
    column_combo = mapping_combo(window, 0, 1)
    column_combo.setCurrentText("NOME")
    window.mapping_page._sync_session_from_table()
    window.mapping_page.refresh_button.click()


def test_mapping_page_tracks_delimiter_detection_and_blocks_generate(prepared_window):
    window = prepared_window.window
    main_window_module = prepared_window.main_window_module

    _go_to_mapping(window)

    placeholder_combo = mapping_combo(window, 0, 0)
    assert placeholder_combo.currentText() == "<<NOME>>"

    _assign_first_mapping(window)
    assert_stage_state(window, 3, blocked=False, completed=False)
    assert window.session.detected_placeholder_delimiter == "<<"
    assert window.session.detected_placeholder_count == 1

    window.mapping_page.delimiter_input.setText("<   ")
    QTest.qWait(250)

    assert window.mapping_page.delimiter_input.text() == "<"
    assert window.session.placeholder_delimiter == "<"
    assert window.session.placeholder_start == "<"
    assert window.session.placeholder_end == ">"
    assert window.session.detected_placeholder_delimiter == "<"
    assert window.session.detected_placeholder_count == 0
    assert_stage_state(window, 3, blocked=True)
    assert window.mapping_page.detected_placeholders == []
    assert window.session.mappings == []
    assert mapping_combo(window, 0, 0).currentText() == ""

    window.mapping_page.delimiter_input.clear()
    assert window.session.placeholder_delimiter == ""
    assert_stage_state(window, 3, blocked=True)

    with patch.object(main_window_module.QMessageBox, "warning") as warning_mock:
        window.mapping_page.next_button.click()

    assert window.stage_manager.currentIndex() == 1
    assert warning_mock.called
    assert "Set a placeholder delimiter before continuing." in warning_mock.call_args.args[2]

    window.mapping_page.delimiter_input.setText("<<")
    QTest.qWait(250)

    assert window.session.placeholder_delimiter == "<<"
    assert_stage_state(window, 3, blocked=True)
    assert mapping_combo(window, 0, 0).currentText() == "<<NOME>>"
    assert window.session.detected_placeholder_delimiter == "<<"
    assert window.session.detected_placeholder_count == 1

    _assign_first_mapping(window)
    assert_stage_state(window, 3, blocked=False)


def test_output_naming_schema_token_insertion_updates_session(prepared_window):
    window = prepared_window.window

    _go_to_mapping(window)
    _assign_first_mapping(window)

    assert window.mapping_page.delimiter_input.text() == "<<"
    assert window.mapping_page.output_naming_schema_input.text() == DEFAULT_OUTPUT_NAMING_SCHEMA
    assert window.mapping_page.output_naming_schema_input.available_tokens() == [
        "NOME",
        "COGNOME",
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
    schema_input.token_completer.activated[str].emit("NOME")
    assert schema_input.text() == "{NOME}"
    assert schema_input.cursorPosition() == len("{NOME}")

    QTest.keyClicks(schema_input, "(mytext){")
    QTest.qWait(80)
    schema_input.token_completer.activated[str].emit("COGNOME")
    assert schema_input.text() == "{NOME}(mytext){COGNOME}"
    assert window.session.output_naming_schema == "{NOME}(mytext){COGNOME}"
    assert_stage_state(window, 3, blocked=False)

    schema_input.setText(DEFAULT_OUTPUT_NAMING_SCHEMA)
    assert window.session.output_naming_schema == DEFAULT_OUTPUT_NAMING_SCHEMA
    assert_stage_state(window, 3, blocked=False)

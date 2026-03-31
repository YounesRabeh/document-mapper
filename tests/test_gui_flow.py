from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QComboBox

from core.certificate.models import DEFAULT_OUTPUT_NAMING_SCHEMA, GenerationResult, MappingEntry, ProjectSession

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class FakeExcelService:
    def inspect(self, _excel_path: str):
        return type("Preview", (), {"columns": ["NOME", "COGNOME"], "row_count": 1})()

    def clear_cache(self, _excel_path: str | None = None):
        return None


class FakeGenerator:
    def __init__(self, _excel_service=None):
        self.result = GenerationResult(
            total_rows=1,
            success_count=1,
            generated_docx_paths=[],
            generated_pdf_paths=[],
            log_path="",
            errors=[],
        )

    def validate_session(self, session):
        errors = []
        if not session.excel_path:
            errors.append("Select an Excel workbook.")
        if not session.template_path:
            errors.append("Select a Word certificate template.")
        if not session.output_dir:
            errors.append("Choose an output folder.")
        if not session.output_naming_schema.strip():
            errors.append("Set an output naming schema before continuing.")
        if not session.placeholder_delimiter.strip():
            errors.append("Set a placeholder delimiter before continuing.")
        elif (
            session.detected_placeholder_delimiter.strip() != session.placeholder_delimiter.strip()
            or session.detected_placeholder_count <= 0
        ):
            errors.append("Refresh and detect at least one placeholder before continuing.")
        if not session.mappings:
            errors.append("Add at least one placeholder mapping.")
        for index, mapping in enumerate(session.mappings, start=1):
            if not mapping.placeholder.strip():
                errors.append(f"Mapping row {index} is missing a placeholder.")
            if not mapping.column_name.strip():
                errors.append(f"Mapping row {index} is missing an Excel column.")
        return errors


class FakeSessionStore:
    def __init__(self):
        self.session = None
        self.loaded_session = None

    def load_last_session(self):
        from core.certificate.models import ProjectSession

        return ProjectSession()

    def save_last_session(self, session):
        self.session = session.clone()
        return Path(tempfile.gettempdir()) / "last_session.json"

    def save(self, session, path):
        self.session = session.clone()
        return Path(path)

    def load(self, _path):
        if self.loaded_session is not None:
            return self.loaded_session.clone()
        return ProjectSession()


class GuiFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def assert_stage_state(self, window, stage_index, *, active=None, blocked=None, completed=None):
        card = window.stage_cards[stage_index]
        if active is not None:
            self.assertEqual(bool(card.property("active")), active)
        if blocked is not None:
            self.assertEqual(bool(card.property("blocked")), blocked)
        if completed is not None:
            self.assertEqual(bool(card.property("completed")), completed)

    def test_main_window_flow_updates_session_and_results(self):
        from gui import main_window as main_window_module

        fake_store = FakeSessionStore()
        config = {
            "APP_NAME": "Document Mapper Test",
            "APP_ORGANIZATION": "Document Mapper Tests",
            "APP_LANGUAGE": "en",
            "WINDOW_WIDTH": 900,
            "WINDOW_HEIGHT": 600,
            "WINDOW_MIN_WIDTH": 800,
            "WINDOW_MIN_HEIGHT": 500,
            "WINDOW_TITLE": "Document Mapper",
            "WINDOW_THEME_MODE": "AUTO",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            workbook = Path(temp_dir) / "data.xlsx"
            template = Path(temp_dir) / "template.docx"
            workbook.write_text("placeholder", encoding="utf-8")
            template.write_text("Hello <<NOME>>", encoding="utf-8")
            QSettings(config["APP_ORGANIZATION"], config["APP_NAME"]).clear()

            with patch.object(main_window_module, "ProjectSessionStore", return_value=fake_store), patch.object(
                main_window_module, "ExcelDataService", return_value=FakeExcelService()
            ), patch.object(main_window_module, "CertificateGenerator", side_effect=lambda _excel: FakeGenerator()):
                window = main_window_module.MainWindow(config)

            self.assertEqual(len(window.stage_cards), 4)
            self.assertEqual(window.sidebar_title.text(), "Workflow")
            self.assert_stage_state(window, 1, active=True, blocked=False, completed=False)
            self.assert_stage_state(window, 2, active=False, blocked=False, completed=False)
            self.assert_stage_state(window, 3, active=False, blocked=True, completed=False)
            self.assert_stage_state(window, 4, active=False, blocked=True, completed=False)

            window.stage_manager.setCurrentIndex(2)
            self.assertEqual(window.stage_manager.currentIndex(), 0)
            self.assert_stage_state(window, 1, active=True, blocked=False, completed=False)

            window.setup_page.excel_input["input"].setText(str(workbook))
            window.setup_page.template_input["input"].setText(str(template))
            window.setup_page.output_input["input"].setText(temp_dir)
            self.assertEqual(window.setup_page.certificate_type_input.count(), 4)
            self.assertEqual(
                window.setup_page.certificate_type_input.itemText(0),
                "MODELLO ATTESTATO integrale PS 12 ORE tipo B e C",
            )
            window.setup_page._sync_session()

            self.assertEqual(window.session.excel_path, str(workbook))
            self.assertEqual(window.session.template_path, str(template))
            self.assertEqual(window.session.output_naming_schema, DEFAULT_OUTPUT_NAMING_SCHEMA)
            self.assertFalse(hasattr(window.setup_page, "output_naming_schema_input"))
            self.assertEqual(window.stage_manager.currentIndex(), 0)
            self.assert_stage_state(window, 3, blocked=True)

            window.stage_cards[2].clicked.emit(2)
            self.assertEqual(window.stage_manager.currentIndex(), 1)
            self.assertTrue(window.stage_cards[2].property("active"))
            self.assert_stage_state(window, 1, completed=True)
            self.assert_stage_state(window, 4, blocked=True)
            self.assertEqual(window.mapping_page.delimiter_input.text(), "<<")
            self.assertEqual(window.mapping_page.output_naming_schema_input.text(), DEFAULT_OUTPUT_NAMING_SCHEMA)
            self.assertEqual(
                window.mapping_page.output_naming_schema_input.available_tokens(),
                ["NOME", "COGNOME", "ROW", "CERTIFICATE_TYPE"],
            )

            window.stage_cards[4].clicked.emit(4)
            self.assertEqual(window.stage_manager.currentIndex(), 1)

            mapping_input = window.mapping_page._get_cell_editor(0, 0, QComboBox)
            self.assertEqual(mapping_input.currentText(), "<<NOME>>")
            column_combo = window.mapping_page._get_cell_editor(0, 1, QComboBox)
            column_combo.setCurrentText("NOME")
            window.mapping_page._sync_session_from_table()
            window.mapping_page.refresh_button.click()

            self.assertEqual(len(window.session.mappings), 1)
            self.assertEqual(window.session.mappings[0].column_name, "NOME")
            self.assert_stage_state(window, 3, blocked=False, completed=False)
            self.assertEqual(window.session.detected_placeholder_delimiter, "<<")
            self.assertEqual(window.session.detected_placeholder_count, 1)

            schema_input = window.mapping_page.output_naming_schema_input
            schema_input.clear()
            self.assertEqual(window.session.output_naming_schema, "")
            self.assert_stage_state(window, 3, blocked=True)
            schema_input.setFocus()
            QTest.keyClicks(schema_input, "{")
            QTest.qWait(80)
            self.assertTrue(schema_input.token_completer.popup().isVisible())
            schema_input.token_completer.activated[str].emit("NOME")
            self.assertEqual(schema_input.text(), "{NOME}")
            self.assertEqual(schema_input.cursorPosition(), len("{NOME}"))
            QTest.keyClicks(schema_input, "(mytext){")
            QTest.qWait(80)
            schema_input.token_completer.activated[str].emit("COGNOME")
            self.assertEqual(schema_input.text(), "{NOME}(mytext){COGNOME}")
            self.assertEqual(window.session.output_naming_schema, "{NOME}(mytext){COGNOME}")
            self.assert_stage_state(window, 3, blocked=False)

            schema_input.setText(DEFAULT_OUTPUT_NAMING_SCHEMA)
            self.assertEqual(window.session.output_naming_schema, DEFAULT_OUTPUT_NAMING_SCHEMA)
            self.assert_stage_state(window, 3, blocked=False)

            window.mapping_page.delimiter_input.setText("<   ")
            QTest.qWait(250)
            self.assertEqual(window.mapping_page.delimiter_input.text(), "<")
            self.assertEqual(window.session.placeholder_delimiter, "<")
            self.assertEqual(window.session.placeholder_start, "<")
            self.assertEqual(window.session.placeholder_end, ">")
            self.assertEqual(window.session.detected_placeholder_delimiter, "<")
            self.assertEqual(window.session.detected_placeholder_count, 0)
            self.assert_stage_state(window, 3, blocked=True)
            self.assertEqual(window.mapping_page.detected_placeholders, [])
            self.assertEqual(window.session.mappings, [])
            self.assertEqual(window.session.detected_placeholder_delimiter, "<")
            self.assertEqual(window.session.detected_placeholder_count, 0)
            self.assert_stage_state(window, 3, blocked=True)
            mapping_input = window.mapping_page._get_cell_editor(0, 0, QComboBox)
            self.assertEqual(mapping_input.currentText(), "")

            window.mapping_page.delimiter_input.clear()
            self.assertEqual(window.session.placeholder_delimiter, "")
            self.assert_stage_state(window, 3, blocked=True)

            with patch.object(main_window_module.QMessageBox, "warning") as warning_mock:
                window.mapping_page.next_button.click()

            self.assertEqual(window.stage_manager.currentIndex(), 1)
            self.assertTrue(warning_mock.called)
            self.assertIn("Set a placeholder delimiter before continuing.", warning_mock.call_args.args[2])

            window.mapping_page.delimiter_input.setText("<<")
            QTest.qWait(250)
            self.assertEqual(window.session.placeholder_delimiter, "<<")
            self.assert_stage_state(window, 3, blocked=True)
            mapping_input = window.mapping_page._get_cell_editor(0, 0, QComboBox)
            self.assertEqual(mapping_input.currentText(), "<<NOME>>")
            self.assertEqual(window.session.detected_placeholder_delimiter, "<<")
            self.assertEqual(window.session.detected_placeholder_count, 1)
            column_combo = window.mapping_page._get_cell_editor(0, 1, QComboBox)
            column_combo.setCurrentText("NOME")
            window.mapping_page._sync_session_from_table()
            self.assert_stage_state(window, 3, blocked=False)

            window.stage_cards[3].clicked.emit(3)
            self.assertEqual(window.stage_manager.currentIndex(), 2)
            self.assert_stage_state(window, 2, completed=True)
            self.assert_stage_state(window, 3, active=True, blocked=False)

            result = GenerationResult(
                total_rows=1,
                success_count=1,
                generated_docx_paths=[str(Path(temp_dir) / "docx" / "ADA_attestato_certificato.docx")],
                generated_pdf_paths=[],
                log_path=str(Path(temp_dir) / "certificate_generation.log"),
                errors=[],
            )
            window._handle_generation_result(result)

            self.assertEqual(window.stage_manager.currentIndex(), 3)
            self.assertIn("Created 1 of 1 DOCX certificates.", window.results_page.summary_label.text())
            self.assert_stage_state(window, 3, completed=True)
            self.assert_stage_state(window, 4, active=True, blocked=False)

            window.localization.set_language("it")
            self.assertEqual(window.view_menu.title(), "Visualizza")
            self.assertEqual(window.setup_page.next_button.text(), "Avanti: Mappatura")
            self.assertIn("esempio", window.mapping_page.mapping_hint.text())
            self.assertEqual(window.mapping_page.output_naming_schema_label.text(), "Schema nome output")
            self.assertIn("Creati 1 certificati DOCX su 1.", window.results_page.summary_label.text())
            self.assert_stage_state(window, 4, active=True, blocked=False)

            window._new_project()
            self.assertEqual(window.stage_manager.currentIndex(), 0)
            self.assert_stage_state(window, 1, active=True, blocked=False, completed=False)
            self.assert_stage_state(window, 3, active=False, blocked=True, completed=False)
            self.assert_stage_state(window, 4, active=False, blocked=True, completed=False)

            fake_store.loaded_session = ProjectSession(
                excel_path=str(workbook),
                template_path=str(template),
                output_dir=temp_dir,
                detected_placeholder_delimiter="<<",
                detected_placeholder_count=1,
                mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
            )
            with patch.object(main_window_module.QFileDialog, "getOpenFileName", return_value=("project.json", "")):
                window._open_project()

            self.assertEqual(window.stage_manager.currentIndex(), 0)
            self.assert_stage_state(window, 1, active=True, blocked=False, completed=False)
            self.assert_stage_state(window, 3, active=False, blocked=False, completed=False)
            self.assert_stage_state(window, 4, active=False, blocked=True, completed=False)


if __name__ == "__main__":
    unittest.main()

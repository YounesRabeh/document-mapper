from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from core.certificate.models import GenerationResult

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


class FakeExcelService:
    def inspect(self, _excel_path: str):
        return type("Preview", (), {"columns": ["NOME", "COGNOME"], "row_count": 1})()


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
        if not session.mappings:
            errors.append("Add at least one placeholder mapping.")
        return errors


class FakeSessionStore:
    def __init__(self):
        self.session = None

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
        from core.certificate.models import ProjectSession

        return ProjectSession()


class GuiFlowTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_main_window_flow_updates_session_and_results(self):
        from gui import main_window as main_window_module

        fake_store = FakeSessionStore()
        config = {
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
            template.write_text("placeholder", encoding="utf-8")

            with patch.object(main_window_module, "ProjectSessionStore", return_value=fake_store), patch.object(
                main_window_module, "ExcelDataService", return_value=FakeExcelService()
            ), patch.object(main_window_module, "CertificateGenerator", side_effect=lambda _excel: FakeGenerator()):
                window = main_window_module.MainWindow(config)

            window.setup_page.excel_input["input"].setPlainText(str(workbook))
            window.setup_page.template_input["input"].setPlainText(str(template))
            window.setup_page.output_input["input"].setPlainText(temp_dir)
            self.assertEqual(window.setup_page.certificate_type_input.count(), 4)
            self.assertEqual(
                window.setup_page.certificate_type_input.itemText(0),
                "MODELLO ATTESTATO integrale PS 12 ORE tipo B e C",
            )
            window.setup_page._sync_session()

            self.assertEqual(window.session.excel_path, str(workbook))
            self.assertEqual(window.session.template_path, str(template))

            window.goto_stage(2)
            mapping_item = window.mapping_page.mapping_table.item(0, 0)
            mapping_item.setText("<<NOME>>")
            column_combo = window.mapping_page.mapping_table.cellWidget(0, 1)
            column_combo.setCurrentText("NOME")
            window.mapping_page._sync_session_from_table()

            self.assertEqual(len(window.session.mappings), 1)
            self.assertEqual(window.session.mappings[0].column_name, "NOME")

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


if __name__ == "__main__":
    unittest.main()

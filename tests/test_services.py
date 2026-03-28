from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from core.certificate.excel_service import ExcelDataService, normalize_column_name
from core.certificate.generator import CertificateGenerator
from core.certificate.models import MappingEntry, ProjectSession
from core.certificate.session_store import ProjectSessionStore


class FakeExcelService:
    def __init__(self, dataframe: pd.DataFrame):
        self.dataframe = dataframe

    def inspect(self, _excel_path: str):
        return SimpleNamespace(columns=[str(column) for column in self.dataframe.columns], row_count=len(self.dataframe.index))

    def read_dataframe(self, _excel_path: str) -> pd.DataFrame:
        return self.dataframe.copy()

    def build_column_lookup(self, columns: list[str]) -> dict[str, str]:
        return {normalize_column_name(column): column for column in columns}

    def validate_mappings(self, columns: list[str], mappings: list[MappingEntry]) -> list[str]:
        return ExcelDataService().validate_mappings(columns, mappings)


class FakeDocument:
    license_value = None

    def __init__(self):
        self.replacements: list[tuple[str, str]] = []
        self.template_path = None

    def LoadFromFile(self, path: str):
        self.template_path = path

    def Replace(self, placeholder: str, value: str, _whole_word: bool, _case_sensitive: bool):
        self.replacements.append((placeholder, value))

    def SaveToFile(self, path: str, _file_format):
        Path(path).write_text("generated", encoding="utf-8")

    def Close(self):
        return None

    @classmethod
    def SetLicense(cls, path: str):
        cls.license_value = path


def fake_spire_dependencies():
    return FakeDocument, SimpleNamespace(Docx2016="Docx2016")


class ServicesTestCase(unittest.TestCase):
    def test_normalize_column_name(self):
        self.assertEqual(normalize_column_name("  nome   completo "), "NOME COMPLETO")

    def test_validate_mappings_uses_normalized_columns(self):
        service = ExcelDataService()
        errors = service.validate_mappings(
            [" Nome ", "COGNOME"],
            [MappingEntry(placeholder="<<NOME>>", column_name="nome")],
        )
        self.assertEqual(errors, [])

    def test_session_store_round_trip(self):
        session = ProjectSession(
            excel_path="/tmp/data.xlsx",
            template_path="/tmp/template.docx",
            output_dir="/tmp/out",
            certificate_type="attestato",
            export_pdf=True,
            mappings=[MappingEntry(placeholder="<<NAME>>", column_name="NOME")],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProjectSessionStore(temp_dir)
            saved_path = store.save(session, Path(temp_dir) / "project.json")
            loaded = store.load(saved_path)

        self.assertEqual(loaded.to_dict(), session.to_dict())

    def test_session_store_loads_legacy_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = ProjectSessionStore(temp_dir)
            config_path = Path(temp_dir) / "config.json"
            setup_path = Path(temp_dir) / "SETUP.json"

            config_path.write_text(
                '{"<<NOME>>": "NOME", "<<COGNOME>>": "COGNOME"}',
                encoding="utf-8",
            )
            setup_path.write_text(
                (
                    '{'
                    '"excel_path": "/tmp/data.xlsx", '
                    '"template_path": "/tmp/template.docx", '
                    '"output_dir": "/tmp/out", '
                    '"license_path": "/tmp/license.xml", '
                    '"certificate_type": "attestato", '
                    '"category": "python", '
                    '"toPDF": true, '
                    '"toPDF_timeout": 180'
                    '}'
                ),
                encoding="utf-8",
            )

            session = store.load_legacy_files(config_path, setup_path)

        self.assertEqual(session.excel_path, "/tmp/data.xlsx")
        self.assertEqual(session.template_path, "/tmp/template.docx")
        self.assertEqual(session.output_dir, "/tmp/out")
        self.assertEqual(session.license_path, "/tmp/license.xml")
        self.assertEqual(session.certificate_type, "attestato")
        self.assertEqual(session.category, "python")
        self.assertTrue(session.export_pdf)
        self.assertEqual(session.pdf_timeout_seconds, 180)
        self.assertEqual(len(session.mappings), 2)
        self.assertEqual(session.mappings[0].placeholder, "<<NOME>>")
        self.assertEqual(session.mappings[0].column_name, "NOME")

    def test_generator_formats_dates_and_creates_docx(self):
        dataframe = pd.DataFrame(
            [
                {
                    "NOME": "Ada",
                    "COGNOME": "Lovelace",
                    "DATA": pd.Timestamp("2026-03-28"),
                    "NUMERO-ATTESTATO": "42A",
                }
            ]
        )
        excel_service = FakeExcelService(dataframe)
        generator = CertificateGenerator(excel_service=excel_service)
        generator._load_spire_dependencies = fake_spire_dependencies  # type: ignore[method-assign]
        generator._clean_docx_content = lambda _path: True  # type: ignore[method-assign]

        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "template.docx"
            template_path.write_text("template", encoding="utf-8")
            session = ProjectSession(
                excel_path=str(Path(temp_dir) / "data.xlsx"),
                template_path=str(template_path),
                output_dir=temp_dir,
                mappings=[
                    MappingEntry(placeholder="<<NOME>>", column_name="NOME"),
                    MappingEntry(placeholder="<<DATA>>", column_name="DATA"),
                ],
            )
            Path(session.excel_path).write_text("placeholder", encoding="utf-8")

            result = generator.generate(session)

            self.assertEqual(result.success_count, 1)
            self.assertEqual(result.last_certificate_number, "42A")
            self.assertEqual(len(result.generated_docx_paths), 1)
            self.assertTrue(Path(result.generated_docx_paths[0]).exists())

    def test_generator_creates_pdfs_when_enabled(self):
        dataframe = pd.DataFrame([{"NOME": "Ada", "COGNOME": "Lovelace"}])

        def fake_runner(command, **_kwargs):
            output_index = command.index("--outdir") + 1
            output_dir = Path(command[output_index])
            for docx_file in command[output_index + 1 :]:
                (output_dir / f"{Path(docx_file).stem}.pdf").write_text("pdf", encoding="utf-8")
            return SimpleNamespace(returncode=0)

        generator = CertificateGenerator(excel_service=FakeExcelService(dataframe), process_runner=fake_runner)
        generator._load_spire_dependencies = fake_spire_dependencies  # type: ignore[method-assign]
        generator._clean_docx_content = lambda _path: True  # type: ignore[method-assign]

        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "template.docx"
            excel_path = Path(temp_dir) / "data.xlsx"
            template_path.write_text("template", encoding="utf-8")
            excel_path.write_text("placeholder", encoding="utf-8")
            session = ProjectSession(
                excel_path=str(excel_path),
                template_path=str(template_path),
                output_dir=temp_dir,
                export_pdf=True,
                mappings=[MappingEntry(placeholder="<<NOME>>", column_name="NOME")],
            )

            result = generator.generate(session)

            self.assertEqual(result.success_count, 1)
            self.assertEqual(len(result.generated_pdf_paths), 1)
            self.assertTrue(Path(result.generated_pdf_paths[0]).exists())

    def test_validate_session_reports_missing_columns(self):
        generator = CertificateGenerator(
            excel_service=FakeExcelService(pd.DataFrame([{"NOME": "Ada"}]))
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "template.docx"
            excel_path = Path(temp_dir) / "data.xlsx"
            template_path.write_text("template", encoding="utf-8")
            excel_path.write_text("placeholder", encoding="utf-8")
            session = ProjectSession(
                excel_path=str(excel_path),
                template_path=str(template_path),
                output_dir=temp_dir,
                mappings=[MappingEntry(placeholder="<<COGNOME>>", column_name="COGNOME")],
            )

            errors = generator.validate_session(session)

            self.assertTrue(any("COGNOME" in error for error in errors))


if __name__ == "__main__":
    unittest.main()

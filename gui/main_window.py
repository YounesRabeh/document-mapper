from pathlib import Path

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStackedWidget

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import GenerationResult, ProjectSession
from core.certificate.session_store import ProjectSessionStore
from core.manager.theme_manager import ThemeManager
from core.util.logger import Logger
from gui.workflow.pages import GeneratePage, MappingPage, ResultsPage, SetupPage

WINDOW_MIN_WIDTH = 960
WINDOW_MIN_HEIGHT = 640


class MainWindow(QMainWindow):
    """Main window for the certificate mail-merge workflow."""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.current_project_path: str | None = None
        self.session_store = ProjectSessionStore()
        self.excel_service = ExcelDataService()
        self.generator = CertificateGenerator(self.excel_service)
        self.session = self.session_store.load_last_session()
        self.last_result = GenerationResult()

        ThemeManager(config)

        min_width = max(self.config.get("WINDOW_MIN_WIDTH", 400), WINDOW_MIN_WIDTH)
        min_height = max(self.config.get("WINDOW_MIN_HEIGHT", 300), WINDOW_MIN_HEIGHT)
        self.resize(
            max(self.config.get("WINDOW_WIDTH", 800), min_width),
            max(self.config.get("WINDOW_HEIGHT", 500), min_height),
        )
        self.setMinimumSize(min_width, min_height)
        self.setWindowTitle(self.config.get("WINDOW_TITLE", "Document Mapper"))

        self.stage_manager = QStackedWidget()
        self.stage_manager.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setCentralWidget(self.stage_manager)

        self.setup_page = SetupPage()
        self.mapping_page = MappingPage(self.excel_service, self.generator)
        self.generate_page = GeneratePage(self.generator)
        self.results_page = ResultsPage()

        self.stage_manager.addWidget(self.setup_page)
        self.stage_manager.addWidget(self.mapping_page)
        self.stage_manager.addWidget(self.generate_page)
        self.stage_manager.addWidget(self.results_page)

        self.setup_page.next_requested.connect(lambda: self.goto_stage(2))
        self.mapping_page.prev_requested.connect(lambda: self.goto_stage(1))
        self.mapping_page.next_requested.connect(lambda: self.goto_stage(3))
        self.generate_page.prev_requested.connect(lambda: self.goto_stage(2))
        self.generate_page.results_ready.connect(self._handle_generation_result)
        self.results_page.prev_requested.connect(lambda: self.goto_stage(3))

        self.setup_page.session_changed.connect(self._persist_last_session)
        self.mapping_page.session_changed.connect(self._persist_last_session)

        self._create_menu_bar()
        self._refresh_pages()
        self.goto_stage(1)

    def _create_menu_bar(self):
        file_menu = self.menuBar().addMenu("File")
        view_menu = self.menuBar().addMenu("View")
        help_menu = self.menuBar().addMenu("Help")

        new_project = QAction("New Project", self)
        open_project = QAction("Open Project...", self)
        save_project = QAction("Save Project", self)
        save_project_as = QAction("Save Project As...", self)
        exit_action = QAction("Exit", self)
        toggle_theme = QAction("Toggle Theme", self)
        about_action = QAction("About", self)

        new_project.triggered.connect(self._new_project)
        open_project.triggered.connect(self._open_project)
        save_project.triggered.connect(self._save_project)
        save_project_as.triggered.connect(self._save_project_as)
        exit_action.triggered.connect(self.close)
        toggle_theme.triggered.connect(ThemeManager.toggle_theme)
        about_action.triggered.connect(self._show_about)

        file_menu.addAction(new_project)
        file_menu.addAction(open_project)
        file_menu.addAction(save_project)
        file_menu.addAction(save_project_as)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        view_menu.addAction(toggle_theme)
        help_menu.addAction(about_action)

    def _refresh_pages(self):
        self.setup_page.bind_session(self.session)
        self.mapping_page.bind_session(self.session)
        self.generate_page.bind_session(self.session)
        self.results_page.bind_result(self.last_result, self.session)

    def _persist_last_session(self):
        self.session_store.save_last_session(self.session)
        self.generate_page.bind_session(self.session)

    def goto_stage(self, index: int):
        self.stage_manager.setCurrentIndex(index - 1)
        if index == 2:
            self.mapping_page.bind_session(self.session)
        elif index == 3:
            self.generate_page.bind_session(self.session)
        elif index == 4:
            self.results_page.bind_result(self.last_result, self.session)
        Logger.debug(f"Switched to workflow page {index}")

    def _new_project(self):
        self.current_project_path = None
        self.last_result = GenerationResult()
        self.session = ProjectSession()
        self._persist_last_session()
        self._refresh_pages()
        self.goto_stage(1)

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open project", "", "Project Files (*.json)")
        if not path:
            return
        try:
            self.session = self.session_store.load(path)
            self.current_project_path = path
            self.last_result = GenerationResult()
            self._persist_last_session()
            self._refresh_pages()
            self.goto_stage(1)
        except Exception as exc:
            QMessageBox.critical(self, "Open project failed", str(exc))

    def _save_project(self):
        if self.current_project_path:
            self.session_store.save(self.session, self.current_project_path)
            return
        self._save_project_as()

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save project",
            self.current_project_path or str(Path.cwd() / "document-mapper-project.json"),
            "Project Files (*.json)",
        )
        if not path:
            return
        self.current_project_path = str(self.session_store.save(self.session, path))

    def _handle_generation_result(self, result: GenerationResult):
        self.last_result = result
        self.results_page.bind_result(result, self.session)
        self.goto_stage(4)

    def _show_about(self):
        QMessageBox.information(
            self,
            "About Document Mapper",
            "Document Mapper creates DOCX certificates from Excel data and optional PDF exports.",
        )

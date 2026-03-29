from pathlib import Path

from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QStackedWidget

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
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
        self.localization = LocalizationManager(config)

        min_width = max(self.config.get("WINDOW_MIN_WIDTH", 400), WINDOW_MIN_WIDTH)
        min_height = max(self.config.get("WINDOW_MIN_HEIGHT", 300), WINDOW_MIN_HEIGHT)
        self.resize(
            max(self.config.get("WINDOW_WIDTH", 800), min_width),
            max(self.config.get("WINDOW_HEIGHT", 500), min_height),
        )
        self.setMinimumSize(min_width, min_height)
        self.setWindowTitle(self.localization.t("app.name"))

        self.stage_manager = QStackedWidget()
        self.stage_manager.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setCentralWidget(self.stage_manager)

        self.setup_page = SetupPage(self.localization)
        self.mapping_page = MappingPage(self.excel_service, self.generator, self.localization)
        self.generate_page = GeneratePage(self.generator, self.localization)
        self.results_page = ResultsPage(self.localization)

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
        self.localization.language_changed.connect(self._retranslate_ui)
        self._refresh_pages()
        self._retranslate_ui()
        self.goto_stage(1)

    def _create_menu_bar(self):
        self.file_menu = self.menuBar().addMenu("")
        self.view_menu = self.menuBar().addMenu("")
        self.help_menu = self.menuBar().addMenu("")
        self.language_menu = self.view_menu.addMenu("")

        self.new_project_action = QAction(self)
        self.open_project_action = QAction(self)
        self.save_project_action = QAction(self)
        self.save_project_as_action = QAction(self)
        self.exit_action = QAction(self)
        self.toggle_theme_action = QAction(self)
        self.about_action = QAction(self)

        self.new_project_action.triggered.connect(self._new_project)
        self.open_project_action.triggered.connect(self._open_project)
        self.save_project_action.triggered.connect(self._save_project)
        self.save_project_as_action.triggered.connect(self._save_project_as)
        self.exit_action.triggered.connect(self.close)
        self.toggle_theme_action.triggered.connect(ThemeManager.toggle_theme)
        self.about_action.triggered.connect(self._show_about)

        self.file_menu.addAction(self.new_project_action)
        self.file_menu.addAction(self.open_project_action)
        self.file_menu.addAction(self.save_project_action)
        self.file_menu.addAction(self.save_project_as_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)

        self.view_menu.addAction(self.toggle_theme_action)
        self.help_menu.addAction(self.about_action)

        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)
        self.language_en_action = QAction(self, checkable=True)
        self.language_it_action = QAction(self, checkable=True)
        self.language_action_group.addAction(self.language_en_action)
        self.language_action_group.addAction(self.language_it_action)
        self.language_en_action.triggered.connect(lambda checked: checked and self.localization.set_language("en"))
        self.language_it_action.triggered.connect(lambda checked: checked and self.localization.set_language("it"))
        self.language_menu.addAction(self.language_en_action)
        self.language_menu.addAction(self.language_it_action)

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
        current_page = self.stage_manager.currentWidget()
        if hasattr(current_page, "scroll_to_top"):
            current_page.scroll_to_top()
        Logger.debug(f"Switched to workflow page {index}")

    def _new_project(self):
        self.current_project_path = None
        self.last_result = GenerationResult()
        self.session = ProjectSession()
        self._persist_last_session()
        self._refresh_pages()
        self.goto_stage(1)

    def _open_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.localization.t("dialog.open_project.title"),
            "",
            self.localization.t("dialog.project_files"),
        )
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
            QMessageBox.critical(self, self.localization.t("dialog.open_project.failed_title"), str(exc))

    def _save_project(self):
        if self.current_project_path:
            self.session_store.save(self.session, self.current_project_path)
            return
        self._save_project_as()

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            self.localization.t("dialog.save_project.title"),
            self.current_project_path or str(Path.cwd() / "document-mapper-project.json"),
            self.localization.t("dialog.project_files"),
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
            self.localization.t("dialog.about.title"),
            self.localization.t("dialog.about.body"),
        )

    def _retranslate_ui(self):
        self.setWindowTitle(self.localization.t("app.name"))
        self.file_menu.setTitle(self.localization.t("menu.file"))
        self.view_menu.setTitle(self.localization.t("menu.view"))
        self.help_menu.setTitle(self.localization.t("menu.help"))
        self.language_menu.setTitle(self.localization.t("menu.language"))

        self.new_project_action.setText(self.localization.t("action.new_project"))
        self.open_project_action.setText(self.localization.t("action.open_project"))
        self.save_project_action.setText(self.localization.t("action.save_project"))
        self.save_project_as_action.setText(self.localization.t("action.save_project_as"))
        self.exit_action.setText(self.localization.t("action.exit"))
        self.toggle_theme_action.setText(self.localization.t("action.toggle_theme"))
        self.about_action.setText(self.localization.t("action.about"))

        self.language_en_action.setText(self.localization.t("menu.language.en"))
        self.language_it_action.setText(self.localization.t("menu.language.it"))
        self.language_en_action.setChecked(self.localization.current_language == "en")
        self.language_it_action.setChecked(self.localization.current_language == "it")

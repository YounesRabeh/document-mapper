from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import GenerationResult, ProjectSession
from core.certificate.session_store import ProjectSessionStore
from core.certificate.template_service import TemplatePlaceholderService
from core.manager.localization_manager import LocalizationManager
from core.manager.theme_manager import ThemeManager
from core.project import ProjectDocument, TemplateCatalogService
from core.util.app_paths import AppPaths
from gui.controllers import WorkflowStateController
from gui.dialogs import TemplateManagerDialog
from gui.styles import MAIN_WINDOW_QSS
from gui.windows.constants import CONTENT_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from gui.windows.project_actions import (
    activate_new_project,
    confirm_new_project_action,
    current_project_dir,
    handle_template_selection_changed,
    handle_template_type_changed,
    manage_templates,
    new_project,
    open_project,
    prepare_session_for_save,
    refresh_template_toolbar,
    save_project,
    save_project_as,
    save_project_to_path,
    show_about,
    sync_effective_template_path,
)
from gui.windows.ui_builders import create_menu_bar, create_sidebar, create_template_toolbar
from gui.windows.workflow_actions import (
    can_navigate_to_stage,
    goto_stage,
    handle_generation_result,
    handle_stage_changed,
    persist_last_session,
    refresh_pages,
    refresh_workflow_state,
    resolve_fallback_stage,
    retranslate_ui,
)
from gui.workflow.pages import GeneratePage, MappingPage, ResultsPage, SetupPage


class MainWindow(QMainWindow):
    """Main window for the template-based document merge workflow."""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config

        self.session_store = ProjectSessionStore()
        self.excel_service = ExcelDataService()
        self.template_service = TemplatePlaceholderService()
        self.generator = CertificateGenerator(self.excel_service)
        self.template_catalog = TemplateCatalogService(AppPaths.default_template_path)
        loaded_session = self.session_store.load_last_session()
        self.template_catalog.seed_default_template(loaded_session)
        self.document = ProjectDocument(session=loaded_session)
        self.workflow_controller = WorkflowStateController(self.generator)

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

        self.window_root = QWidget()
        self.window_root.setObjectName("windowRoot")
        self.window_root.setStyleSheet(MAIN_WINDOW_QSS)
        self.setCentralWidget(self.window_root)

        root_layout = QHBoxLayout(self.window_root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        root_layout.addWidget(self.sidebar)

        self.content_root = QWidget()
        content_layout = QVBoxLayout(self.content_root)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        root_layout.addWidget(self.content_root, stretch=1)

        self.template_toolbar = self._create_template_toolbar()
        content_layout.addWidget(self.template_toolbar)

        self.stage_manager = QStackedWidget()
        self.stage_manager.setMinimumWidth(CONTENT_MIN_WIDTH)
        self.stage_manager.setMinimumHeight(0)
        self.stage_manager.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout.addWidget(self.stage_manager, stretch=1)

        self.setup_page = SetupPage(self.localization)
        self.mapping_page = MappingPage(
            self.excel_service,
            self.generator,
            self.localization,
            self.template_service,
        )
        self.generate_page = GeneratePage(self.generator, self.localization)
        self.results_page = ResultsPage(self.localization)

        self.stage_manager.addWidget(self.setup_page)
        self.stage_manager.addWidget(self.mapping_page)
        self.stage_manager.addWidget(self.generate_page)
        self.stage_manager.addWidget(self.results_page)
        self._last_valid_stage = 1
        self.stage_manager.currentChanged.connect(self._handle_stage_changed)

        self.generate_page.results_ready.connect(self._handle_generation_result)
        self.setup_page.session_changed.connect(self._persist_last_session)
        self.mapping_page.session_changed.connect(self._persist_last_session)

        self._create_menu_bar()
        self.localization.language_changed.connect(self._retranslate_ui)
        self._refresh_pages()
        self._retranslate_ui()
        self.goto_stage(1)

    @property
    def session(self) -> ProjectSession:
        return self.document.session

    @session.setter
    def session(self, value: ProjectSession):
        self.document.session = value

    @property
    def current_project_path(self) -> str | None:
        return self.document.project_path

    @current_project_path.setter
    def current_project_path(self, value: str | None):
        self.document.project_path = value

    @property
    def last_result(self) -> GenerationResult:
        return self.document.last_result

    @last_result.setter
    def last_result(self, value: GenerationResult):
        self.document.last_result = value

    def _create_sidebar(self):
        return create_sidebar(self)

    def _create_template_toolbar(self):
        return create_template_toolbar(self)

    def _create_menu_bar(self):
        create_menu_bar(self)

    def _refresh_pages(self):
        refresh_pages(self)

    def _persist_last_session(self):
        persist_last_session(self)

    def goto_stage(self, index: int):
        return goto_stage(self, index)

    def _new_project(self):
        new_project(self)

    def _open_project(self):
        open_project(self, file_dialog_cls=QFileDialog, message_box_cls=QMessageBox, app_paths_cls=AppPaths)

    def _save_project(self):
        return save_project(self)

    def _save_project_as(self):
        return save_project_as(self, file_dialog_cls=QFileDialog, app_paths_cls=AppPaths)

    def _save_project_to_path(self, path):
        return save_project_to_path(self, path)

    def _activate_new_project(self, session: ProjectSession, *, saved: bool):
        activate_new_project(self, session, saved=saved)

    def _confirm_new_project_action(self) -> str | None:
        return confirm_new_project_action(self, message_box_cls=QMessageBox)

    def _prepare_session_for_save(self, project_dir):
        return prepare_session_for_save(self, project_dir, message_box_cls=QMessageBox)

    def _current_project_dir(self):
        return current_project_dir(self)

    def _sync_effective_template_path(self, session: ProjectSession | None = None):
        sync_effective_template_path(self, session)

    def _refresh_template_toolbar(self):
        refresh_template_toolbar(self)

    def _handle_template_type_changed(self, index: int):
        handle_template_type_changed(self, index)

    def _handle_template_selection_changed(self, index: int):
        handle_template_selection_changed(self, index)

    def _manage_templates(self):
        manage_templates(self, dialog_cls=TemplateManagerDialog, accepted_code=QDialog.DialogCode.Accepted)

    def _handle_generation_result(self, result: GenerationResult):
        handle_generation_result(self, result)

    def _show_about(self):
        show_about(self, message_box_cls=QMessageBox)

    def _retranslate_ui(self):
        retranslate_ui(self)

    def _handle_stage_changed(self, current_index: int):
        handle_stage_changed(self, current_index)

    def _refresh_workflow_state(self):
        refresh_workflow_state(self)

    def _can_navigate_to_stage(self, index: int) -> bool:
        return can_navigate_to_stage(self, index)

    def _resolve_fallback_stage(self) -> int:
        return resolve_fallback_stage(self)

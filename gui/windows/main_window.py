from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QActionGroup
from PySide6.QtWidgets import (
    QDialog,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
)

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import GenerationResult, ProjectSession
from core.certificate.session_store import ProjectSessionStore
from core.certificate.template_service import TemplatePlaceholderService
from core.enums.app_themes import AppTheme
from core.manager.localization_manager import LocalizationManager
from core.manager.theme_manager import ThemeManager
from core.project import ProjectDocument, TemplateCatalogService
from core.util.app_paths import AppPaths
from gui.controllers import WorkflowStateController
from gui.dialogs import TemplateManagerDialog
from gui.forms import Ui_MainWindow
from gui.styles import apply_stylesheet
from gui.windows.components import SidebarStageCard
from gui.windows.constants import CONTENT_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH
from gui.windows.last_session_persistence import LastSessionPersistenceService
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
    THEME_PERSIST_DEBOUNCE_MS = 300
    LAST_SESSION_FLUSH_TIMEOUT_SECONDS = 2.0

    def __init__(self, config: dict):
        super().__init__()
        self.config = dict(config)
        self.default_theme_mode = self._normalize_theme_mode(
            self.config.get("WINDOW_THEME_MODE", AppTheme.AUTO)
        ) or AppTheme.AUTO.name

        self.session_store = ProjectSessionStore()
        self.excel_service = ExcelDataService()
        self.template_service = TemplatePlaceholderService()
        self.generator = CertificateGenerator(self.excel_service)
        self.template_catalog = TemplateCatalogService(AppPaths.default_template_path)
        loaded_session = self.session_store.load_last_session()
        self.template_catalog.seed_default_template(loaded_session)
        self.document = ProjectDocument(session=loaded_session)
        self.workflow_controller = WorkflowStateController(self.generator)

        initial_theme_mode = self.session.theme_mode or self.default_theme_mode
        self.theme_manager = ThemeManager({**self.config, "WINDOW_THEME_MODE": initial_theme_mode})
        self.localization = LocalizationManager(config)
        self._applying_project_theme = False
        self._theme_persist_timer = QTimer(self)
        self._theme_persist_timer.setSingleShot(True)
        self._theme_persist_timer.setInterval(self.THEME_PERSIST_DEBOUNCE_MS)
        self._theme_persist_timer.timeout.connect(self._flush_theme_session_persist)
        self._last_session_persistence = LastSessionPersistenceService(self.session_store)

        min_width = max(self.config.get("WINDOW_MIN_WIDTH", 400), WINDOW_MIN_WIDTH)
        min_height = max(self.config.get("WINDOW_MIN_HEIGHT", 300), WINDOW_MIN_HEIGHT)
        self.resize(
            max(self.config.get("WINDOW_WIDTH", 800), min_width),
            max(self.config.get("WINDOW_HEIGHT", 500), min_height),
        )
        self.setMinimumSize(min_width, min_height)
        self.setWindowTitle(self.localization.t("app.name"))

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        apply_stylesheet(self, "main_window")

        self.window_root = self.ui.windowRoot
        self.sidebar = self.ui.workflowSidebarScroll
        self.sidebar_eyebrow = self.ui.sidebarEyebrow
        self.sidebar_title = self.ui.sidebarTitle
        self.sidebar_subtitle = self.ui.sidebarSubtitle
        self.stage_cards_layout = self.ui.stageCardsLayout
        self.template_toolbar = self.ui.templateToolbar
        self.template_type_label = self.ui.templateTypeLabel
        self.template_type_combo = self.ui.templateTypeCombo
        self.template_label = self.ui.templateLabel
        self.template_combo = self.ui.templateCombo
        self.manage_templates_button = self.ui.manageTemplatesButton
        self.template_toolbar_status = self.ui.templateToolbarStatus
        self.stage_manager = self.ui.stageManager
        self.file_menu = self.ui.menuFile
        self.view_menu = self.ui.menuView
        self.help_menu = self.ui.menuHelp
        self.language_menu = self.ui.menuLanguage
        self.new_project_action = self.ui.actionNewProject
        self.open_project_action = self.ui.actionOpenProject
        self.save_project_action = self.ui.actionSaveProject
        self.save_project_as_action = self.ui.actionSaveProjectAs
        self.exit_action = self.ui.actionExit
        self.toggle_theme_action = self.ui.actionToggleTheme
        self.about_action = self.ui.actionAbout
        self.language_en_action = self.ui.actionLanguageEn
        self.language_it_action = self.ui.actionLanguageIt

        self.ui.workflowSidebar.setObjectName("workflowSidebar")
        self.template_type_label.setObjectName("templateToolbarLabel")
        self.template_label.setObjectName("templateToolbarLabel")
        self.template_type_combo.setObjectName("templateToolbarCombo")
        self.template_combo.setObjectName("templateToolbarCombo")
        self.manage_templates_button.setObjectName("templateToolbarButton")
        self.template_toolbar_status.setObjectName("templateToolbarStatus")

        self.stage_manager.setMinimumWidth(CONTENT_MIN_WIDTH)
        self.stage_manager.setMinimumHeight(0)
        self.stage_manager.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.stage_cards = {}
        for index, title_key, detail_key in (
            (1, "sidebar.stage.setup", "sidebar.stage.setup.detail"),
            (2, "sidebar.stage.mapping", "sidebar.stage.mapping.detail"),
            (3, "sidebar.stage.generate", "sidebar.stage.generate.detail"),
            (4, "sidebar.stage.results", "sidebar.stage.results.detail"),
        ):
            card = SidebarStageCard(index, title_key, detail_key, self.localization)
            card.clicked.connect(self.goto_stage)
            self.stage_cards[index] = card
            self.stage_cards_layout.addWidget(card)

        self.template_type_combo.currentIndexChanged.connect(self._handle_template_type_changed)
        self.template_combo.currentIndexChanged.connect(self._handle_template_selection_changed)
        self.manage_templates_button.clicked.connect(self._manage_templates)

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
        self.theme_manager.theme_changed.connect(self._handle_theme_changed)
        self.localization.language_changed.connect(self._retranslate_ui)
        self._apply_project_theme_mode(
            initial_theme_mode,
            persist_to_session=True,
            save_last_session=False,
            sync_document_snapshot=True,
        )
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

    def _create_menu_bar(self):
        self.new_project_action.triggered.connect(self._new_project)
        self.open_project_action.triggered.connect(self._open_project)
        self.save_project_action.triggered.connect(self._save_project)
        self.save_project_as_action.triggered.connect(self._save_project_as)
        self.exit_action.triggered.connect(self.close)
        self.toggle_theme_action.triggered.connect(self._toggle_theme)
        self.about_action.triggered.connect(self._show_about)

        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)
        self.language_action_group.addAction(self.language_en_action)
        self.language_action_group.addAction(self.language_it_action)
        self.language_en_action.triggered.connect(
            lambda checked: checked and self.localization.set_language("en")
        )
        self.language_it_action.triggered.connect(
            lambda checked: checked and self.localization.set_language("it")
        )

    def _refresh_pages(self):
        refresh_pages(self)

    def _persist_last_session(self):
        persist_last_session(self)

    def goto_stage(self, index: int):
        return goto_stage(self, index)

    def _new_project(self):
        new_project(self)

    def _open_project(self):
        open_project(self, file_dialog_cls=None, message_box_cls=QMessageBox, app_paths_cls=AppPaths)

    def _save_project(self):
        return save_project(self, message_box_cls=QMessageBox, app_paths_cls=AppPaths)

    def _save_project_as(self, *, message_box_cls=QMessageBox):
        return save_project_as(
            self,
            file_dialog_cls=None,
            app_paths_cls=AppPaths,
            message_box_cls=message_box_cls,
        )

    def _save_project_to_path(self, path, *, message_box_cls=QMessageBox):
        return save_project_to_path(self, path, message_box_cls=message_box_cls)

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

    def _toggle_theme(self):
        ThemeManager.toggle_theme()

    def _handle_theme_changed(self, theme: AppTheme):
        if self._applying_project_theme:
            return
        normalized = theme.name
        if self.session.theme_mode == normalized:
            return
        self.session.theme_mode = normalized
        self._schedule_theme_session_persist()

    def _apply_project_theme_mode(
        self,
        theme_mode: str | AppTheme | None,
        *,
        persist_to_session: bool = True,
        save_last_session: bool = True,
        sync_document_snapshot: bool = False,
    ):
        normalized = self._normalize_theme_mode(theme_mode) or self.default_theme_mode
        self._applying_project_theme = True
        try:
            ThemeManager.set_canonical_theme(AppTheme[normalized])
        finally:
            self._applying_project_theme = False

        if persist_to_session:
            self.session.theme_mode = normalized
        if sync_document_snapshot:
            self.document.mark_saved()
        if save_last_session:
            self._persist_last_session_async()

    def _schedule_theme_session_persist(self):
        self._theme_persist_timer.start()

    def _flush_theme_session_persist(self):
        if self.session.theme_mode:
            self._persist_last_session_async()

    def _persist_last_session_async(self):
        self._last_session_persistence.enqueue(self.session.clone())

    def _confirm_close_action(self) -> str | None:
        if not self.document.is_dirty:
            return "discard"

        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Icon.Question)
        message_box.setWindowTitle(self.localization.t("dialog.close_project_confirm.title"))
        message_box.setText(self.localization.t("dialog.close_project_confirm.body"))
        save_button = message_box.addButton(
            self.localization.t("dialog.close_project_confirm.save"),
            QMessageBox.ButtonRole.AcceptRole,
        )
        discard_button = message_box.addButton(
            self.localization.t("dialog.close_project_confirm.discard"),
            QMessageBox.ButtonRole.DestructiveRole,
        )
        cancel_button = message_box.addButton(
            self.localization.t("dialog.close_project_confirm.cancel"),
            QMessageBox.ButtonRole.RejectRole,
        )
        message_box.exec()

        clicked_button = message_box.clickedButton()
        if clicked_button is save_button:
            return "save"
        if clicked_button is discard_button:
            return "discard"
        if clicked_button is cancel_button:
            return None
        return None

    @staticmethod
    def _normalize_theme_mode(value: str | AppTheme | None) -> str:
        if isinstance(value, AppTheme):
            return value.name
        candidate = str(value or "").strip().upper()
        return candidate if candidate in AppTheme.__members__ else ""

    def closeEvent(self, event):
        action = self._confirm_close_action()
        if action is None:
            event.ignore()
            return
        if action == "save" and not self._save_project():
            event.ignore()
            return
        if self._theme_persist_timer.isActive():
            self._theme_persist_timer.stop()
        if action == "discard":
            baseline_session = self.document.saved_session() or ProjectSession(
                theme_mode=self.default_theme_mode
            )
            self._last_session_persistence.enqueue(baseline_session)
        else:
            self._persist_last_session_async()
        flushed = self._last_session_persistence.flush_and_stop(self.LAST_SESSION_FLUSH_TIMEOUT_SECONDS)
        if not flushed:
            fallback_snapshot = self._last_session_persistence.latest_snapshot() or (
                self.document.saved_session() if action == "discard" else self.session.clone()
            )
            if fallback_snapshot is None:
                fallback_snapshot = ProjectSession(theme_mode=self.default_theme_mode)
            try:
                self.session_store.save_last_session(fallback_snapshot)
            except Exception:  # noqa: BLE001
                pass
        super().closeEvent(event)

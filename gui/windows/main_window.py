from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.certificate.excel_service import ExcelDataService
from core.certificate.generator import CertificateGenerator
from core.certificate.models import (
    DEFAULT_IMPORTED_TEMPLATE_TYPE,
    DEFAULT_IMPORTED_TEMPLATE_NAME,
    GenerationResult,
    ProjectSession,
    ProjectTemplateEntry,
    ProjectTemplateType,
    normalize_template_name,
)
from core.certificate.session_store import ProjectSessionStore
from core.certificate.template_service import TemplatePlaceholderService
from core.manager.localization_manager import LocalizationManager
from core.manager.theme_manager import ThemeManager
from core.util.app_paths import AppPaths
from core.util.logger import Logger
from gui.dialogs import TemplateManagerDialog
from gui.styles import MAIN_WINDOW_QSS
from gui.ui.elements.combo_box import ClickSelectComboBox
from gui.workflow.pages import GeneratePage, MappingPage, ResultsPage, SetupPage

SIDEBAR_WIDTH = 296
CONTENT_MIN_WIDTH = 860
WINDOW_MIN_WIDTH = 1240
WINDOW_MIN_HEIGHT = 680


@dataclass(slots=True)
class WorkflowStageState:
    active: bool = False
    completed: bool = False
    blocked: bool = False


class SidebarStageCard(QFrame):
    clicked = Signal(int)

    def __init__(self, stage_index: int, title_key: str, detail_key: str, localization: LocalizationManager):
        super().__init__()
        self.stage_index = stage_index
        self.title_key = title_key
        self.detail_key = detail_key
        self.localization = localization

        self.setObjectName("sidebarStageCard")
        self.setProperty("active", False)
        self.setProperty("completed", False)
        self.setProperty("blocked", False)
        self._blocked = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(82)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        self.index_label = QLabel()
        self.index_label.setObjectName("sidebarStageIndex")
        self.index_label.setAlignment(Qt.AlignCenter)
        self.index_label.setFixedSize(34, 28)
        self.index_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(5)

        self.title_label = QLabel()
        self.title_label.setObjectName("sidebarStageTitle")
        self.title_label.setWordWrap(True)
        self.title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.detail_label = QLabel()
        self.detail_label.setObjectName("sidebarStageDetail")
        self.detail_label.setWordWrap(True)
        self.detail_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)

        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.detail_label)

        layout.addWidget(self.index_label, alignment=Qt.AlignTop)
        layout.addLayout(text_layout, stretch=1)

        self.retranslate()

    def retranslate(self):
        self.index_label.setText(f"{self.stage_index:02d}")
        self.title_label.setText(self.localization.t(self.title_key))
        self.detail_label.setText(self.localization.t(self.detail_key))

    def set_stage_state(self, state: WorkflowStageState):
        self._blocked = state.blocked
        self.setProperty("active", state.active)
        self.setProperty("completed", state.completed)
        self.setProperty("blocked", state.blocked)
        self.setCursor(Qt.ArrowCursor if state.blocked else Qt.PointingHandCursor)
        for widget in (self, self.index_label, self.title_label, self.detail_label):
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._blocked:
            self.clicked.emit(self.stage_index)
        super().mousePressEvent(event)


class MainWindow(QMainWindow):
    """Main window for the template-based document merge workflow."""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.current_project_path: str | None = None

        self.session_store = ProjectSessionStore()
        self.excel_service = ExcelDataService()
        self.template_service = TemplatePlaceholderService()
        self.generator = CertificateGenerator(self.excel_service)
        self.session = self.session_store.load_last_session()
        self._ensure_default_template_seeded(self.session)
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
        self.stage_manager.setMinimumSize(CONTENT_MIN_WIDTH, WINDOW_MIN_HEIGHT)
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

    def _create_sidebar(self) -> QScrollArea:
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setObjectName("workflowSidebarScroll")
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFrameShape(QFrame.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setFixedWidth(SIDEBAR_WIDTH)

        sidebar = QFrame()
        sidebar.setObjectName("workflowSidebar")
        sidebar_scroll.setWidget(sidebar)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(22, 24, 22, 24)
        layout.setSpacing(14)

        self.sidebar_eyebrow = QLabel("WORKFLOW")
        self.sidebar_eyebrow.setObjectName("sidebarEyebrow")

        self.sidebar_title = QLabel()
        self.sidebar_title.setObjectName("sidebarTitle")

        self.sidebar_subtitle = QLabel()
        self.sidebar_subtitle.setObjectName("sidebarSubtitle")
        self.sidebar_subtitle.setWordWrap(True)

        layout.addWidget(self.sidebar_eyebrow)
        layout.addWidget(self.sidebar_title)
        layout.addWidget(self.sidebar_subtitle)

        self.stage_cards: dict[int, SidebarStageCard] = {}
        for index, title_key, detail_key in (
            (1, "sidebar.stage.setup", "sidebar.stage.setup.detail"),
            (2, "sidebar.stage.mapping", "sidebar.stage.mapping.detail"),
            (3, "sidebar.stage.generate", "sidebar.stage.generate.detail"),
            (4, "sidebar.stage.results", "sidebar.stage.results.detail"),
        ):
            card = SidebarStageCard(index, title_key, detail_key, self.localization)
            card.clicked.connect(self.goto_stage)
            self.stage_cards[index] = card
            layout.addWidget(card)

        layout.addStretch(1)

        self.sidebar_new_button = QPushButton()
        self.sidebar_open_button = QPushButton()
        self.sidebar_save_button = QPushButton()
        for button in (self.sidebar_new_button, self.sidebar_open_button, self.sidebar_save_button):
            button.setObjectName("sidebarUtilityButton")
            button.setMinimumHeight(44)
        self.sidebar_new_button.clicked.connect(self._new_project)
        self.sidebar_open_button.clicked.connect(self._open_project)
        self.sidebar_save_button.clicked.connect(self._save_project)

        layout.addWidget(self.sidebar_new_button)
        layout.addWidget(self.sidebar_open_button)
        layout.addWidget(self.sidebar_save_button)

        return sidebar_scroll

    def _create_template_toolbar(self) -> QFrame:
        toolbar = QFrame()
        toolbar.setObjectName("templateToolbar")

        layout = QVBoxLayout(toolbar)
        layout.setContentsMargins(24, 16, 24, 14)
        layout.setSpacing(10)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        self.template_type_label = QLabel()
        self.template_type_label.setObjectName("templateToolbarLabel")
        self.template_type_combo = ClickSelectComboBox()
        self.template_type_combo.setObjectName("templateToolbarCombo")
        self.template_type_combo.currentIndexChanged.connect(self._handle_template_type_changed)

        self.template_label = QLabel()
        self.template_label.setObjectName("templateToolbarLabel")
        self.template_combo = ClickSelectComboBox()
        self.template_combo.setObjectName("templateToolbarCombo")
        self.template_combo.currentIndexChanged.connect(self._handle_template_selection_changed)

        self.manage_templates_button = QPushButton()
        self.manage_templates_button.setObjectName("templateToolbarButton")
        self.manage_templates_button.clicked.connect(self._manage_templates)

        row.addWidget(self.template_type_label)
        row.addWidget(self.template_type_combo)
        row.addWidget(self.template_label)
        row.addWidget(self.template_combo)
        row.addStretch(1)
        row.addWidget(self.manage_templates_button)

        self.template_toolbar_status = QLabel()
        self.template_toolbar_status.setObjectName("templateToolbarStatus")
        self.template_toolbar_status.setWordWrap(True)

        layout.addLayout(row)
        layout.addWidget(self.template_toolbar_status)
        return toolbar

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
        self._sync_effective_template_path()
        self._refresh_template_toolbar()
        self.setup_page.bind_session(self.session)
        self.mapping_page.bind_session(self.session)
        self.generate_page.bind_session(self.session)
        self.results_page.bind_result(self.last_result, self.session)
        self._refresh_workflow_state()

    def _persist_last_session(self):
        self._sync_effective_template_path()
        self.session_store.save_last_session(self.session)
        self._refresh_template_toolbar()
        self.generate_page.bind_session(self.session)
        self.results_page.bind_result(self.last_result, self.session)
        self._refresh_workflow_state()

    def goto_stage(self, index: int):
        if index < 1 or index > self.stage_manager.count():
            return False
        if not self._can_navigate_to_stage(index):
            self._refresh_workflow_state()
            return False
        target_index = index - 1
        if self.stage_manager.currentIndex() == target_index:
            self._handle_stage_changed(target_index)
            return True
        self.stage_manager.setCurrentIndex(target_index)
        return True

    def _new_project(self):
        self.current_project_path = None
        self.last_result = GenerationResult()
        self.session = ProjectSession()
        self._ensure_default_template_seeded(self.session)
        self.session_store.save_last_session(self.session)
        self._refresh_pages()
        self.goto_stage(1)

    def _open_project(self):
        start_dir = self.current_project_path or str(AppPaths.documents_dir())
        path = QFileDialog.getExistingDirectory(
            self,
            self.localization.t("dialog.open_project.title"),
            start_dir,
        )
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self.localization.t("dialog.open_project.title"),
                start_dir,
                self.localization.t("dialog.project_files"),
            )
        if not path:
            return
        try:
            self.session = self.session_store.load(path)
            self._ensure_default_template_seeded(self.session)
            selected_path = Path(path).expanduser().resolve()
            self.current_project_path = str(selected_path if selected_path.is_dir() else selected_path.parent)
            self.last_result = GenerationResult()
            self.session_store.save_last_session(self.session)
            self._refresh_pages()
            self.goto_stage(1)
        except Exception as exc:
            QMessageBox.critical(self, self.localization.t("dialog.open_project.failed_title"), str(exc))

    def _save_project(self):
        if self.current_project_path:
            self._save_project_to_path(self.current_project_path)
            return
        self._save_project_as()

    def _save_project_as(self):
        path = QFileDialog.getExistingDirectory(
            self,
            self.localization.t("dialog.save_project.title"),
            self.current_project_path or str(AppPaths.default_project_path()),
        )
        if not path:
            return
        self._save_project_to_path(path)

    def _save_project_to_path(self, path: str | Path):
        project_dir = Path(path).expanduser().resolve()
        session_to_save = self._prepare_session_for_save(project_dir)
        if session_to_save is None:
            return

        saved_path = self.session_store.save(session_to_save, project_dir)
        self.current_project_path = str(Path(saved_path).parent)
        self.session = self.session_store.load(self.current_project_path)
        self.session_store.save_last_session(self.session)
        self._refresh_pages()

    def _prepare_session_for_save(self, project_dir: Path) -> ProjectSession | None:
        session_to_save = self.session.clone()
        if not session_to_save.template_override_path:
            self._sync_effective_template_path(session_to_save)
            return session_to_save

        override_path = Path(session_to_save.template_override_path).expanduser()
        if not override_path.exists():
            self._sync_effective_template_path(session_to_save)
            return session_to_save

        message_box = QMessageBox(self)
        message_box.setIcon(QMessageBox.Question)
        message_box.setWindowTitle(self.localization.t("dialog.template_override_save.title"))
        message_box.setText(
            self.localization.t(
                "dialog.template_override_save.body",
                path=override_path.name,
            )
        )
        store_button = message_box.addButton(
            self.localization.t("dialog.template_override_save.store"),
            QMessageBox.AcceptRole,
        )
        keep_button = message_box.addButton(
            self.localization.t("dialog.template_override_save.keep"),
            QMessageBox.DestructiveRole,
        )
        cancel_button = message_box.addButton(
            self.localization.t("dialog.template_override_save.cancel"),
            QMessageBox.RejectRole,
        )
        message_box.exec()

        clicked_button = message_box.clickedButton()
        if clicked_button is cancel_button:
            return None
        if clicked_button is store_button:
            self._store_template_override_in_project(session_to_save)

        self._sync_effective_template_path(session_to_save)
        return session_to_save

    def _ensure_default_template_seeded(self, session: ProjectSession):
        if session.templates:
            return

        default_template_path = AppPaths.shipped_test_template_path()
        if default_template_path is None:
            return

        default_type = ProjectTemplateType(DEFAULT_IMPORTED_TEMPLATE_TYPE)
        default_entry = ProjectTemplateEntry(
            display_name=DEFAULT_IMPORTED_TEMPLATE_NAME,
            type_name=default_type.name,
            source_path=str(default_template_path),
            is_managed=False,
        )
        session.template_types = [default_type]
        session.templates = [default_entry]
        session.selected_template_type = default_type.name
        session.selected_template = default_entry.id
        session.template_path = str(default_template_path)

    def _store_template_override_in_project(self, session: ProjectSession):
        if not session.template_override_path:
            return
        override_path = Path(session.template_override_path).expanduser().resolve()
        if not override_path.exists():
            return

        type_name = session.selected_template_type or DEFAULT_IMPORTED_TEMPLATE_TYPE
        if type_name not in {entry.name for entry in session.template_types}:
            session.template_types.append(ProjectTemplateType(type_name))

        display_name = self._unique_template_display_name(
            session,
            type_name,
            normalize_template_name(override_path.stem) or normalize_template_name(override_path.name),
        )
        new_entry = ProjectTemplateEntry(
            display_name=display_name,
            type_name=type_name,
            source_path=str(override_path),
            is_managed=False,
        )
        session.templates.append(new_entry)
        session.selected_template_type = type_name
        session.selected_template = new_entry.id
        session.template_override_path = ""
        session._ensure_template_catalog_consistency()

    def _unique_template_display_name(
        self,
        session: ProjectSession,
        type_name: str,
        base_name: str,
        exclude_template_id: str = "",
    ) -> str:
        normalized = normalize_template_name(base_name) or "Template"
        existing = {
            entry.label.casefold()
            for entry in session.templates_for_type(type_name)
            if entry.id != exclude_template_id
        }
        candidate = normalized
        counter = 2
        while candidate.casefold() in existing:
            candidate = f"{normalized} {counter}"
            counter += 1
        return candidate

    def _current_project_dir(self) -> Path | None:
        if not self.current_project_path:
            return None
        return Path(self.current_project_path).expanduser().resolve()

    def _sync_effective_template_path(self, session: ProjectSession | None = None):
        target_session = session or self.session
        target_session.template_path = self.session_store.resolve_effective_template_path(
            target_session,
            self._current_project_dir(),
        )

    def _refresh_template_toolbar(self):
        selected_type = self.session.selected_template_type
        type_names = [entry.name for entry in self.session.template_types]

        self.template_type_combo.blockSignals(True)
        self.template_combo.blockSignals(True)
        try:
            self.template_type_combo.clear()
            for type_name in type_names:
                self.template_type_combo.addItem(type_name, type_name)

            if selected_type:
                index = self.template_type_combo.findData(selected_type)
                if index >= 0:
                    self.template_type_combo.setCurrentIndex(index)
            elif self.template_type_combo.count() > 0:
                self.template_type_combo.setCurrentIndex(0)

            current_type = self.session.selected_template_type
            template_entries = self.session.templates_for_type(current_type)
            self.template_combo.clear()
            for entry in template_entries:
                self.template_combo.addItem(entry.label, entry.id)

            if self.session.selected_template:
                index = self.template_combo.findData(self.session.selected_template)
                if index >= 0:
                    self.template_combo.setCurrentIndex(index)
            elif self.template_combo.count() > 0:
                self.template_combo.setCurrentIndex(0)

            has_types = bool(type_names)
            has_templates = bool(template_entries)
            self.template_type_combo.setEnabled(has_types)
            self.template_combo.setEnabled(has_templates)

            if self.session.template_override_path:
                self.template_toolbar_status.setText(
                    self.localization.t(
                        "status.template_override_active",
                        name=Path(self.session.template_override_path).name,
                    )
                )
            elif not has_types:
                self.template_toolbar_status.setText(self.localization.t("status.no_project_templates"))
            elif not has_templates:
                self.template_toolbar_status.setText(self.localization.t("status.no_templates_for_selected_type"))
            else:
                self.template_toolbar_status.setText(
                    self.localization.t(
                        "status.active_template_ready",
                        name=self.session.active_template_name or self.localization.t("common.not_selected"),
                    )
                )
        finally:
            self.template_type_combo.blockSignals(False)
            self.template_combo.blockSignals(False)

    def _handle_template_type_changed(self, _index: int):
        selected_type = str(self.template_type_combo.currentData() or "").strip()
        if selected_type == self.session.selected_template_type:
            return

        self.session.selected_template_type = selected_type
        template_entries = self.session.templates_for_type(selected_type)
        self.session.selected_template = template_entries[0].id if template_entries else ""
        self._persist_last_session()
        self.setup_page.refresh_from_session()
        self.mapping_page.bind_session(self.session)

    def _handle_template_selection_changed(self, _index: int):
        selected_template = str(self.template_combo.currentData() or "").strip()
        if selected_template == self.session.selected_template:
            return
        self.session.selected_template = selected_template
        self._persist_last_session()
        self.setup_page.refresh_from_session()
        self.mapping_page.bind_session(self.session)

    def _manage_templates(self):
        dialog = TemplateManagerDialog(self.session, self.localization, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        self.session = dialog.edited_session()
        self._sync_effective_template_path()
        self.session_store.save_last_session(self.session)
        self._refresh_pages()

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
        self.sidebar_title.setText(self.localization.t("sidebar.heading"))
        self.sidebar_subtitle.setText(self.localization.t("sidebar.subtitle"))
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
        self.sidebar_new_button.setText(self.localization.t("action.new_project"))
        self.sidebar_open_button.setText(self.localization.t("action.open_project"))
        self.sidebar_save_button.setText(self.localization.t("action.save_project"))
        self.template_type_label.setText(self.localization.t("field.template_type"))
        self.template_label.setText(self.localization.t("field.template"))
        self.manage_templates_button.setText(self.localization.t("button.manage_templates"))

        self.language_en_action.setText(self.localization.t("menu.language.en"))
        self.language_it_action.setText(self.localization.t("menu.language.it"))
        self.language_en_action.setChecked(self.localization.current_language == "en")
        self.language_it_action.setChecked(self.localization.current_language == "it")
        for card in self.stage_cards.values():
            card.retranslate()
        self._refresh_template_toolbar()
        self._refresh_workflow_state()

    def _handle_stage_changed(self, current_index: int):
        stage_number = current_index + 1
        if not self._can_navigate_to_stage(stage_number):
            fallback_stage = self._resolve_fallback_stage()
            if fallback_stage != stage_number:
                self.stage_manager.blockSignals(True)
                self.stage_manager.setCurrentIndex(fallback_stage - 1)
                self.stage_manager.blockSignals(False)
            self._handle_stage_changed(fallback_stage - 1)
            return

        self._last_valid_stage = stage_number
        if stage_number == 2:
            self.mapping_page.bind_session(self.session)
        elif stage_number == 3:
            self.generate_page.bind_session(self.session)
        elif stage_number == 4:
            self.results_page.bind_result(self.last_result, self.session)
        current_page = self.stage_manager.currentWidget()
        if hasattr(current_page, "scroll_to_top"):
            current_page.scroll_to_top()
        self._refresh_workflow_state()
        Logger.debug(f"Switched to workflow page {stage_number}")

    def _refresh_workflow_state(self):
        states = self._compute_workflow_states()
        for index, card in self.stage_cards.items():
            card.set_stage_state(states[index])

    def _compute_workflow_states(self) -> dict[int, WorkflowStageState]:
        current_stage = max(1, min(self.stage_manager.currentIndex() + 1, self.stage_manager.count() or 1))
        generate_available = not self.generator.validate_session(self.session)
        results_available = self._has_generation_results()
        blocked_by_stage = {
            1: False,
            2: False,
            3: not generate_available,
            4: not results_available,
        }
        return {
            index: WorkflowStageState(
                active=index == current_stage and not blocked_by_stage[index],
                completed=index < current_stage and not blocked_by_stage[index],
                blocked=blocked_by_stage[index],
            )
            for index in range(1, self.stage_manager.count() + 1)
        }

    def _can_navigate_to_stage(self, index: int) -> bool:
        if index < 1 or index > self.stage_manager.count():
            return False
        return not self._compute_workflow_states()[index].blocked

    def _resolve_fallback_stage(self) -> int:
        if self._can_navigate_to_stage(self._last_valid_stage):
            return self._last_valid_stage
        for stage in range(self.stage_manager.count(), 0, -1):
            if self._can_navigate_to_stage(stage):
                return stage
        return 1

    def _has_generation_results(self) -> bool:
        return any(
            (
                self.last_result.total_rows,
                self.last_result.generated_docx_paths,
                self.last_result.generated_pdf_paths,
                self.last_result.log_path,
                self.last_result.errors,
            )
        )

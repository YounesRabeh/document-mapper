from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
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
from core.certificate.models import GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
from core.certificate.session_store import ProjectSessionStore
from core.manager.theme_manager import ThemeManager
from core.util.logger import Logger
from gui.workflow.pages import GeneratePage, MappingPage, ResultsPage, SetupPage

SIDEBAR_WIDTH = 296
CONTENT_MIN_WIDTH = 860
WINDOW_MIN_WIDTH = 1180
WINDOW_MIN_HEIGHT = 640

MAIN_WINDOW_QSS = """
QWidget#windowRoot {
    background: palette(window);
}

QScrollArea#workflowSidebarScroll {
    background: palette(alternate-base);
    border: none;
    border-right: 1px solid palette(midlight);
}

QScrollArea#workflowSidebarScroll > QWidget > QWidget {
    background: palette(alternate-base);
}

QFrame#workflowSidebar {
    background: palette(alternate-base);
    border: none;
}

QLabel#sidebarEyebrow {
    color: palette(mid);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.1px;
}

QLabel#sidebarTitle {
    color: palette(window-text);
    font-size: 22px;
    font-weight: 800;
}

QLabel#sidebarSubtitle {
    color: palette(text);
    font-size: 13px;
    line-height: 1.45;
}

QFrame#sidebarStageCard {
    background: transparent;
    border: 1px solid transparent;
    border-radius: 16px;
}

QFrame#sidebarStageCard:hover {
    background: palette(button);
    border-color: palette(midlight);
}

QFrame#sidebarStageCard[active="true"] {
    background: palette(button);
    border-color: palette(highlight);
}

QLabel#sidebarStageIndex {
    background: palette(base);
    color: palette(text);
    border-radius: 14px;
    padding: 6px 0;
    font-size: 11px;
    font-weight: 800;
}

QFrame#sidebarStageCard[active="true"] QLabel#sidebarStageIndex {
    background: palette(highlight);
    color: palette(highlighted-text);
}

QLabel#sidebarStageTitle {
    color: palette(window-text);
    font-size: 15px;
    font-weight: 800;
}

QLabel#sidebarStageDetail {
    color: palette(text);
    font-size: 12px;
    opacity: 0.85;
}

QFrame#sidebarStageCard[active="true"] QLabel#sidebarStageDetail {
    color: palette(window-text);
}

QFrame#sidebarStageCard:hover QLabel#sidebarStageDetail {
    color: palette(window-text);
}

QPushButton#sidebarUtilityButton {
    background: palette(base);
    border: 1px solid palette(mid);
    border-radius: 12px;
    color: palette(button-text);
    font-weight: 600;
    padding: 10px 12px;
}

QPushButton#sidebarUtilityButton:hover {
    border-color: palette(highlight);
    background: palette(button);
}
"""


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

    def set_active(self, active: bool):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.stage_index)
        super().mousePressEvent(event)


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

        self.window_root = QWidget()
        self.window_root.setObjectName("windowRoot")
        self.window_root.setStyleSheet(MAIN_WINDOW_QSS)
        self.setCentralWidget(self.window_root)

        root_layout = QHBoxLayout(self.window_root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = self._create_sidebar()
        root_layout.addWidget(self.sidebar)

        self.stage_manager = QStackedWidget()
        self.stage_manager.setMinimumSize(CONTENT_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        root_layout.addWidget(self.stage_manager, stretch=1)

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
        self._set_active_stage(index)
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

        self.language_en_action.setText(self.localization.t("menu.language.en"))
        self.language_it_action.setText(self.localization.t("menu.language.it"))
        self.language_en_action.setChecked(self.localization.current_language == "en")
        self.language_it_action.setChecked(self.localization.current_language == "it")
        for card in self.stage_cards.values():
            card.retranslate()

    def _set_active_stage(self, active_index: int):
        for index, card in self.stage_cards.items():
            card.set_active(index == active_index)

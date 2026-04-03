from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from core.manager.theme_manager import ThemeManager
from gui.ui.elements.combo_box import ClickSelectComboBox
from gui.windows.components import SidebarStageCard
from gui.windows.constants import SIDEBAR_WIDTH


def create_sidebar(window) -> QScrollArea:
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

    window.sidebar_eyebrow = QLabel("WORKFLOW")
    window.sidebar_eyebrow.setObjectName("sidebarEyebrow")

    window.sidebar_title = QLabel()
    window.sidebar_title.setObjectName("sidebarTitle")

    window.sidebar_subtitle = QLabel()
    window.sidebar_subtitle.setObjectName("sidebarSubtitle")
    window.sidebar_subtitle.setWordWrap(True)

    layout.addWidget(window.sidebar_eyebrow)
    layout.addWidget(window.sidebar_title)
    layout.addWidget(window.sidebar_subtitle)

    window.stage_cards = {}
    for index, title_key, detail_key in (
        (1, "sidebar.stage.setup", "sidebar.stage.setup.detail"),
        (2, "sidebar.stage.mapping", "sidebar.stage.mapping.detail"),
        (3, "sidebar.stage.generate", "sidebar.stage.generate.detail"),
        (4, "sidebar.stage.results", "sidebar.stage.results.detail"),
    ):
        card = SidebarStageCard(index, title_key, detail_key, window.localization)
        card.clicked.connect(window.goto_stage)
        window.stage_cards[index] = card
        layout.addWidget(card)

    layout.addStretch(1)

    window.sidebar_new_button = QPushButton()
    window.sidebar_open_button = QPushButton()
    window.sidebar_save_button = QPushButton()
    for button in (window.sidebar_new_button, window.sidebar_open_button, window.sidebar_save_button):
        button.setObjectName("sidebarUtilityButton")
        button.setMinimumHeight(44)
    window.sidebar_new_button.clicked.connect(window._new_project)
    window.sidebar_open_button.clicked.connect(window._open_project)
    window.sidebar_save_button.clicked.connect(window._save_project)

    layout.addWidget(window.sidebar_new_button)
    layout.addWidget(window.sidebar_open_button)
    layout.addWidget(window.sidebar_save_button)

    return sidebar_scroll


def create_template_toolbar(window) -> QFrame:
    toolbar = QFrame()
    toolbar.setObjectName("templateToolbar")

    layout = QVBoxLayout(toolbar)
    layout.setContentsMargins(24, 16, 24, 14)
    layout.setSpacing(10)

    row = QHBoxLayout()
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(12)

    window.template_type_label = QLabel()
    window.template_type_label.setObjectName("templateToolbarLabel")
    window.template_type_combo = ClickSelectComboBox()
    window.template_type_combo.setObjectName("templateToolbarCombo")
    window.template_type_combo.currentIndexChanged.connect(window._handle_template_type_changed)

    window.template_label = QLabel()
    window.template_label.setObjectName("templateToolbarLabel")
    window.template_combo = ClickSelectComboBox()
    window.template_combo.setObjectName("templateToolbarCombo")
    window.template_combo.currentIndexChanged.connect(window._handle_template_selection_changed)

    window.manage_templates_button = QPushButton()
    window.manage_templates_button.setObjectName("templateToolbarButton")
    window.manage_templates_button.clicked.connect(window._manage_templates)

    row.addWidget(window.template_type_label)
    row.addWidget(window.template_type_combo)
    row.addWidget(window.template_label)
    row.addWidget(window.template_combo)
    row.addStretch(1)
    row.addWidget(window.manage_templates_button)

    window.template_toolbar_status = QLabel()
    window.template_toolbar_status.setObjectName("templateToolbarStatus")
    window.template_toolbar_status.setWordWrap(True)

    layout.addLayout(row)
    layout.addWidget(window.template_toolbar_status)
    return toolbar


def create_menu_bar(window):
    window.file_menu = window.menuBar().addMenu("")
    window.view_menu = window.menuBar().addMenu("")
    window.help_menu = window.menuBar().addMenu("")
    window.language_menu = window.view_menu.addMenu("")

    window.new_project_action = QAction(window)
    window.open_project_action = QAction(window)
    window.save_project_action = QAction(window)
    window.save_project_as_action = QAction(window)
    window.exit_action = QAction(window)
    window.toggle_theme_action = QAction(window)
    window.about_action = QAction(window)

    window.new_project_action.triggered.connect(window._new_project)
    window.open_project_action.triggered.connect(window._open_project)
    window.save_project_action.triggered.connect(window._save_project)
    window.save_project_as_action.triggered.connect(window._save_project_as)
    window.exit_action.triggered.connect(window.close)
    window.toggle_theme_action.triggered.connect(ThemeManager.toggle_theme)
    window.about_action.triggered.connect(window._show_about)

    window.file_menu.addAction(window.new_project_action)
    window.file_menu.addAction(window.open_project_action)
    window.file_menu.addAction(window.save_project_action)
    window.file_menu.addAction(window.save_project_as_action)
    window.file_menu.addSeparator()
    window.file_menu.addAction(window.exit_action)

    window.view_menu.addAction(window.toggle_theme_action)
    window.help_menu.addAction(window.about_action)

    window.language_action_group = QActionGroup(window)
    window.language_action_group.setExclusive(True)
    window.language_en_action = QAction(window, checkable=True)
    window.language_it_action = QAction(window, checkable=True)
    window.language_action_group.addAction(window.language_en_action)
    window.language_action_group.addAction(window.language_it_action)
    window.language_en_action.triggered.connect(
        lambda checked: checked and window.localization.set_language("en")
    )
    window.language_it_action.triggered.connect(
        lambda checked: checked and window.localization.set_language("it")
    )
    window.language_menu.addAction(window.language_en_action)
    window.language_menu.addAction(window.language_it_action)

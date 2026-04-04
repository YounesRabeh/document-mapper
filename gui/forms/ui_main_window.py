# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QStackedWidget,
    QVBoxLayout, QWidget)

from gui.ui.elements.combo_box import ClickSelectComboBox

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1280, 760)
        self.actionOpenProject = QAction(MainWindow)
        self.actionOpenProject.setObjectName(u"actionOpenProject")
        self.actionSaveProject = QAction(MainWindow)
        self.actionSaveProject.setObjectName(u"actionSaveProject")
        self.actionSaveProjectAs = QAction(MainWindow)
        self.actionSaveProjectAs.setObjectName(u"actionSaveProjectAs")
        self.actionExit = QAction(MainWindow)
        self.actionExit.setObjectName(u"actionExit")
        self.actionToggleTheme = QAction(MainWindow)
        self.actionToggleTheme.setObjectName(u"actionToggleTheme")
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.actionLanguageEn = QAction(MainWindow)
        self.actionLanguageEn.setObjectName(u"actionLanguageEn")
        self.actionLanguageEn.setCheckable(True)
        self.actionLanguageIt = QAction(MainWindow)
        self.actionLanguageIt.setObjectName(u"actionLanguageIt")
        self.actionLanguageIt.setCheckable(True)
        self.windowRoot = QWidget(MainWindow)
        self.windowRoot.setObjectName(u"windowRoot")
        self.rootLayout = QHBoxLayout(self.windowRoot)
        self.rootLayout.setSpacing(0)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.workflowSidebarScroll = QScrollArea(self.windowRoot)
        self.workflowSidebarScroll.setObjectName(u"workflowSidebarScroll")
        self.workflowSidebarScroll.setMinimumSize(QSize(296, 0))
        self.workflowSidebarScroll.setMaximumSize(QSize(296, 16777215))
        self.workflowSidebarScroll.setFrameShape(QFrame.NoFrame)
        self.workflowSidebarScroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.workflowSidebarScroll.setWidgetResizable(True)
        self.workflowSidebar = QFrame()
        self.workflowSidebar.setObjectName(u"workflowSidebar")
        self.workflowSidebar.setFrameShape(QFrame.NoFrame)
        self.sidebarLayout = QVBoxLayout(self.workflowSidebar)
        self.sidebarLayout.setSpacing(14)
        self.sidebarLayout.setObjectName(u"sidebarLayout")
        self.sidebarLayout.setContentsMargins(22, 24, 22, 24)
        self.sidebarEyebrow = QLabel(self.workflowSidebar)
        self.sidebarEyebrow.setObjectName(u"sidebarEyebrow")

        self.sidebarLayout.addWidget(self.sidebarEyebrow)

        self.sidebarTitle = QLabel(self.workflowSidebar)
        self.sidebarTitle.setObjectName(u"sidebarTitle")

        self.sidebarLayout.addWidget(self.sidebarTitle)

        self.sidebarSubtitle = QLabel(self.workflowSidebar)
        self.sidebarSubtitle.setObjectName(u"sidebarSubtitle")
        self.sidebarSubtitle.setWordWrap(True)

        self.sidebarLayout.addWidget(self.sidebarSubtitle)

        self.stageCardsContainer = QWidget(self.workflowSidebar)
        self.stageCardsContainer.setObjectName(u"stageCardsContainer")
        self.stageCardsLayout = QVBoxLayout(self.stageCardsContainer)
        self.stageCardsLayout.setSpacing(14)
        self.stageCardsLayout.setObjectName(u"stageCardsLayout")
        self.stageCardsLayout.setContentsMargins(0, 0, 0, 0)

        self.sidebarLayout.addWidget(self.stageCardsContainer)

        self.sidebarSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.sidebarLayout.addItem(self.sidebarSpacer)

        self.workflowSidebarScroll.setWidget(self.workflowSidebar)

        self.rootLayout.addWidget(self.workflowSidebarScroll)

        self.contentRoot = QWidget(self.windowRoot)
        self.contentRoot.setObjectName(u"contentRoot")
        self.contentLayout = QVBoxLayout(self.contentRoot)
        self.contentLayout.setSpacing(0)
        self.contentLayout.setObjectName(u"contentLayout")
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.templateToolbar = QFrame(self.contentRoot)
        self.templateToolbar.setObjectName(u"templateToolbar")
        self.templateToolbarLayout = QVBoxLayout(self.templateToolbar)
        self.templateToolbarLayout.setSpacing(10)
        self.templateToolbarLayout.setObjectName(u"templateToolbarLayout")
        self.templateToolbarLayout.setContentsMargins(24, 16, 24, 14)
        self.templateToolbarRow = QHBoxLayout()
        self.templateToolbarRow.setSpacing(12)
        self.templateToolbarRow.setObjectName(u"templateToolbarRow")
        self.templateTypeLabel = QLabel(self.templateToolbar)
        self.templateTypeLabel.setObjectName(u"templateTypeLabel")

        self.templateToolbarRow.addWidget(self.templateTypeLabel)

        self.templateTypeCombo = ClickSelectComboBox(self.templateToolbar)
        self.templateTypeCombo.setObjectName(u"templateTypeCombo")

        self.templateToolbarRow.addWidget(self.templateTypeCombo)

        self.templateLabel = QLabel(self.templateToolbar)
        self.templateLabel.setObjectName(u"templateLabel")

        self.templateToolbarRow.addWidget(self.templateLabel)

        self.templateCombo = ClickSelectComboBox(self.templateToolbar)
        self.templateCombo.setObjectName(u"templateCombo")

        self.templateToolbarRow.addWidget(self.templateCombo)

        self.toolbarStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.templateToolbarRow.addItem(self.toolbarStretch)

        self.manageTemplatesButton = QPushButton(self.templateToolbar)
        self.manageTemplatesButton.setObjectName(u"manageTemplatesButton")

        self.templateToolbarRow.addWidget(self.manageTemplatesButton)


        self.templateToolbarLayout.addLayout(self.templateToolbarRow)

        self.templateToolbarStatus = QLabel(self.templateToolbar)
        self.templateToolbarStatus.setObjectName(u"templateToolbarStatus")
        self.templateToolbarStatus.setWordWrap(True)

        self.templateToolbarLayout.addWidget(self.templateToolbarStatus)


        self.contentLayout.addWidget(self.templateToolbar)

        self.stageManager = QStackedWidget(self.contentRoot)
        self.stageManager.setObjectName(u"stageManager")
        self.stageManager.setMinimumSize(QSize(860, 0))

        self.contentLayout.addWidget(self.stageManager)


        self.rootLayout.addWidget(self.contentRoot)

        MainWindow.setCentralWidget(self.windowRoot)
        self.menuBar = QMenuBar(MainWindow)
        self.menuBar.setObjectName(u"menuBar")
        self.menuBar.setGeometry(QRect(0, 0, 1280, 22))
        self.menuFile = QMenu(self.menuBar)
        self.menuFile.setObjectName(u"menuFile")
        self.menuLanguage = QMenu(self.menuBar)
        self.menuLanguage.setObjectName(u"menuLanguage")
        self.menuView = QMenu(self.menuBar)
        self.menuView.setObjectName(u"menuView")
        self.menuHelp = QMenu(self.menuBar)
        self.menuHelp.setObjectName(u"menuHelp")
        MainWindow.setMenuBar(self.menuBar)

        self.menuBar.addAction(self.menuFile.menuAction())
        self.menuBar.addAction(self.menuView.menuAction())
        self.menuBar.addAction(self.menuHelp.menuAction())
        self.menuFile.addAction(self.actionOpenProject)
        self.menuFile.addAction(self.actionSaveProject)
        self.menuFile.addAction(self.actionSaveProjectAs)
        self.menuFile.addSeparator()
        self.menuFile.addAction(self.actionExit)
        self.menuLanguage.addAction(self.actionLanguageEn)
        self.menuLanguage.addAction(self.actionLanguageIt)
        self.menuView.addAction(self.menuLanguage.menuAction())
        self.menuView.addAction(self.actionToggleTheme)
        self.menuHelp.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Document Mapper", None))
        self.actionOpenProject.setText(QCoreApplication.translate("MainWindow", u"Open project", None))
        self.actionSaveProject.setText(QCoreApplication.translate("MainWindow", u"Save project", None))
        self.actionSaveProjectAs.setText(QCoreApplication.translate("MainWindow", u"Save project as...", None))
        self.actionExit.setText(QCoreApplication.translate("MainWindow", u"Exit", None))
        self.actionToggleTheme.setText(QCoreApplication.translate("MainWindow", u"Toggle theme", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.actionLanguageEn.setText(QCoreApplication.translate("MainWindow", u"English", None))
        self.actionLanguageIt.setText(QCoreApplication.translate("MainWindow", u"Italiano", None))
        self.sidebarEyebrow.setText(QCoreApplication.translate("MainWindow", u"WORKFLOW", None))
        self.sidebarTitle.setText(QCoreApplication.translate("MainWindow", u"Workflow", None))
        self.sidebarSubtitle.setText(QCoreApplication.translate("MainWindow", u"Configure, map, generate, and review each batch.", None))
        self.templateTypeLabel.setText(QCoreApplication.translate("MainWindow", u"Template type", None))
        self.templateLabel.setText(QCoreApplication.translate("MainWindow", u"Template", None))
        self.manageTemplatesButton.setText(QCoreApplication.translate("MainWindow", u"Manage templates...", None))
        self.templateToolbarStatus.setText(QCoreApplication.translate("MainWindow", u"Active template", None))
        self.menuFile.setTitle(QCoreApplication.translate("MainWindow", u"File", None))
        self.menuLanguage.setTitle(QCoreApplication.translate("MainWindow", u"Language", None))
        self.menuView.setTitle(QCoreApplication.translate("MainWindow", u"View", None))
        self.menuHelp.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

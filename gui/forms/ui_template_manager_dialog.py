# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'template_manager_dialog.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_TemplateManagerDialog(object):
    def setupUi(self, TemplateManagerDialog):
        if not TemplateManagerDialog.objectName():
            TemplateManagerDialog.setObjectName(u"TemplateManagerDialog")
        TemplateManagerDialog.resize(860, 480)
        self.rootLayout = QVBoxLayout(TemplateManagerDialog)
        self.rootLayout.setSpacing(12)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(16, 16, 16, 16)
        self.panelsLayout = QHBoxLayout()
        self.panelsLayout.setSpacing(16)
        self.panelsLayout.setObjectName(u"panelsLayout")
        self.typePanel = QWidget(TemplateManagerDialog)
        self.typePanel.setObjectName(u"typePanel")
        self.typeLayout = QVBoxLayout(self.typePanel)
        self.typeLayout.setSpacing(8)
        self.typeLayout.setObjectName(u"typeLayout")
        self.typeLayout.setContentsMargins(0, 0, 0, 0)
        self.typeTitle = QLabel(self.typePanel)
        self.typeTitle.setObjectName(u"typeTitle")

        self.typeLayout.addWidget(self.typeTitle)

        self.typeList = QListWidget(self.typePanel)
        self.typeList.setObjectName(u"typeList")

        self.typeLayout.addWidget(self.typeList)

        self.typeButtonsLayout = QHBoxLayout()
        self.typeButtonsLayout.setObjectName(u"typeButtonsLayout")
        self.typeAddButton = QPushButton(self.typePanel)
        self.typeAddButton.setObjectName(u"typeAddButton")

        self.typeButtonsLayout.addWidget(self.typeAddButton)

        self.typeRenameButton = QPushButton(self.typePanel)
        self.typeRenameButton.setObjectName(u"typeRenameButton")

        self.typeButtonsLayout.addWidget(self.typeRenameButton)

        self.typeRemoveButton = QPushButton(self.typePanel)
        self.typeRemoveButton.setObjectName(u"typeRemoveButton")

        self.typeButtonsLayout.addWidget(self.typeRemoveButton)


        self.typeLayout.addLayout(self.typeButtonsLayout)


        self.panelsLayout.addWidget(self.typePanel)

        self.templatePanel = QWidget(TemplateManagerDialog)
        self.templatePanel.setObjectName(u"templatePanel")
        self.templateLayout = QVBoxLayout(self.templatePanel)
        self.templateLayout.setSpacing(8)
        self.templateLayout.setObjectName(u"templateLayout")
        self.templateLayout.setContentsMargins(0, 0, 0, 0)
        self.templateTitle = QLabel(self.templatePanel)
        self.templateTitle.setObjectName(u"templateTitle")

        self.templateLayout.addWidget(self.templateTitle)

        self.templateList = QListWidget(self.templatePanel)
        self.templateList.setObjectName(u"templateList")

        self.templateLayout.addWidget(self.templateList)

        self.templateButtonsLayout = QHBoxLayout()
        self.templateButtonsLayout.setObjectName(u"templateButtonsLayout")
        self.templateAddButton = QPushButton(self.templatePanel)
        self.templateAddButton.setObjectName(u"templateAddButton")

        self.templateButtonsLayout.addWidget(self.templateAddButton)

        self.templateRenameButton = QPushButton(self.templatePanel)
        self.templateRenameButton.setObjectName(u"templateRenameButton")

        self.templateButtonsLayout.addWidget(self.templateRenameButton)

        self.templateRemoveButton = QPushButton(self.templatePanel)
        self.templateRemoveButton.setObjectName(u"templateRemoveButton")

        self.templateButtonsLayout.addWidget(self.templateRemoveButton)


        self.templateLayout.addLayout(self.templateButtonsLayout)


        self.panelsLayout.addWidget(self.templatePanel)


        self.rootLayout.addLayout(self.panelsLayout)

        self.statusLabel = QLabel(TemplateManagerDialog)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setWordWrap(True)

        self.rootLayout.addWidget(self.statusLabel)

        self.footerLayout = QHBoxLayout()
        self.footerLayout.setObjectName(u"footerLayout")
        self.footerSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.footerLayout.addItem(self.footerSpacer)

        self.cancelButton = QPushButton(TemplateManagerDialog)
        self.cancelButton.setObjectName(u"cancelButton")

        self.footerLayout.addWidget(self.cancelButton)

        self.saveButton = QPushButton(TemplateManagerDialog)
        self.saveButton.setObjectName(u"saveButton")

        self.footerLayout.addWidget(self.saveButton)


        self.rootLayout.addLayout(self.footerLayout)


        self.retranslateUi(TemplateManagerDialog)

        QMetaObject.connectSlotsByName(TemplateManagerDialog)
    # setupUi

    def retranslateUi(self, TemplateManagerDialog):
        TemplateManagerDialog.setWindowTitle(QCoreApplication.translate("TemplateManagerDialog", u"Manage templates", None))
        self.typeTitle.setText(QCoreApplication.translate("TemplateManagerDialog", u"Template types", None))
        self.typeAddButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Add type", None))
        self.typeRenameButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Rename type", None))
        self.typeRemoveButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Remove type", None))
        self.templateTitle.setText(QCoreApplication.translate("TemplateManagerDialog", u"Templates", None))
        self.templateAddButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Import template", None))
        self.templateRenameButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Rename template", None))
        self.templateRemoveButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Remove template", None))
        self.statusLabel.setText(QCoreApplication.translate("TemplateManagerDialog", u"Status", None))
        self.cancelButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Cancel", None))
        self.saveButton.setText(QCoreApplication.translate("TemplateManagerDialog", u"Save", None))
    # retranslateUi


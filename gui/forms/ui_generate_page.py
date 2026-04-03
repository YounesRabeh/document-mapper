# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'generate_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_GeneratePageForm(object):
    def setupUi(self, generatePageForm):
        if not generatePageForm.objectName():
            generatePageForm.setObjectName(u"generatePageForm")
        self.rootLayout = QVBoxLayout(generatePageForm)
        self.rootLayout.setSpacing(16)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.summaryBox = QFrame(generatePageForm)
        self.summaryBox.setObjectName(u"summaryBox")
        self.summaryBox.setFrameShape(QFrame.StyledPanel)
        self.summaryBox.setObjectName(u"workflowCard")
        self.summaryLayout = QVBoxLayout(self.summaryBox)
        self.summaryLayout.setSpacing(14)
        self.summaryLayout.setObjectName(u"summaryLayout")
        self.summaryLayout.setContentsMargins(18, 16, 18, 16)
        self.summaryTitleBar = QFrame(self.summaryBox)
        self.summaryTitleBar.setObjectName(u"summaryTitleBar")
        self.summaryTitleBar.setFrameShape(QFrame.NoFrame)
        self.summaryTitleBar.setObjectName(u"workflowCardTitleBar")
        self.summaryTitleLayout = QHBoxLayout(self.summaryTitleBar)
        self.summaryTitleLayout.setSpacing(0)
        self.summaryTitleLayout.setObjectName(u"summaryTitleLayout")
        self.summaryTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.summaryTitle = QLabel(self.summaryTitleBar)
        self.summaryTitle.setObjectName(u"summaryTitle")
        self.summaryTitle.setObjectName(u"workflowCardTitle")

        self.summaryTitleLayout.addWidget(self.summaryTitle)


        self.summaryLayout.addWidget(self.summaryTitleBar)

        self.summaryOutput = QLabel(self.summaryBox)
        self.summaryOutput.setObjectName(u"summaryOutput")
        self.summaryOutput.setObjectName(u"workflowInfoBox")
        self.summaryOutput.setWordWrap(True)

        self.summaryLayout.addWidget(self.summaryOutput)


        self.rootLayout.addWidget(self.summaryBox)

        self.logBox = QFrame(generatePageForm)
        self.logBox.setObjectName(u"logBox")
        self.logBox.setFrameShape(QFrame.StyledPanel)
        self.logBox.setObjectName(u"workflowCard")
        self.logLayout = QVBoxLayout(self.logBox)
        self.logLayout.setSpacing(14)
        self.logLayout.setObjectName(u"logLayout")
        self.logLayout.setContentsMargins(18, 16, 18, 16)
        self.logTitleBar = QFrame(self.logBox)
        self.logTitleBar.setObjectName(u"logTitleBar")
        self.logTitleBar.setFrameShape(QFrame.NoFrame)
        self.logTitleBar.setObjectName(u"workflowCardTitleBar")
        self.logTitleLayout = QHBoxLayout(self.logTitleBar)
        self.logTitleLayout.setSpacing(0)
        self.logTitleLayout.setObjectName(u"logTitleLayout")
        self.logTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.logTitle = QLabel(self.logTitleBar)
        self.logTitle.setObjectName(u"logTitle")
        self.logTitle.setObjectName(u"workflowCardTitle")

        self.logTitleLayout.addWidget(self.logTitle)


        self.logLayout.addWidget(self.logTitleBar)

        self.logOutput = QPlainTextEdit(self.logBox)
        self.logOutput.setObjectName(u"logOutput")
        self.logOutput.setMinimumSize(QSize(0, 190))

        self.logLayout.addWidget(self.logOutput)


        self.rootLayout.addWidget(self.logBox)

        self.actionRow = QHBoxLayout()
        self.actionRow.setObjectName(u"actionRow")
        self.actionStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionRow.addItem(self.actionStretch)

        self.generateButton = QPushButton(generatePageForm)
        self.generateButton.setObjectName(u"generateButton")

        self.actionRow.addWidget(self.generateButton)


        self.rootLayout.addLayout(self.actionRow)


        self.retranslateUi(generatePageForm)

        QMetaObject.connectSlotsByName(generatePageForm)
    # setupUi

    def retranslateUi(self, generatePageForm):
        self.summaryTitle.setText(QCoreApplication.translate("GeneratePageForm", u"Batch summary", None))
        self.summaryOutput.setText(QCoreApplication.translate("GeneratePageForm", u"Summary", None))
        self.logTitle.setText(QCoreApplication.translate("GeneratePageForm", u"Generation log", None))
        self.generateButton.setText(QCoreApplication.translate("GeneratePageForm", u"Generate documents", None))
        pass
    # retranslateUi


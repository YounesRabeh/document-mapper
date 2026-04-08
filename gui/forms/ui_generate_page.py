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
        self.rootLayout.setSpacing(18)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.summaryCard = QFrame(generatePageForm)
        self.summaryCard.setObjectName(u"summaryCard")
        self.summaryCard.setFrameShape(QFrame.StyledPanel)
        self.summaryLayout = QVBoxLayout(self.summaryCard)
        self.summaryLayout.setSpacing(14)
        self.summaryLayout.setObjectName(u"summaryLayout")
        self.summaryLayout.setContentsMargins(20, 18, 20, 18)
        self.summaryTitleBar = QFrame(self.summaryCard)
        self.summaryTitleBar.setObjectName(u"summaryTitleBar")
        self.summaryTitleBar.setFrameShape(QFrame.NoFrame)
        self.summaryTitleLayout = QHBoxLayout(self.summaryTitleBar)
        self.summaryTitleLayout.setSpacing(0)
        self.summaryTitleLayout.setObjectName(u"summaryTitleLayout")
        self.summaryTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.summaryTitle = QLabel(self.summaryTitleBar)
        self.summaryTitle.setObjectName(u"summaryTitle")

        self.summaryTitleLayout.addWidget(self.summaryTitle)


        self.summaryLayout.addWidget(self.summaryTitleBar)

        self.summaryStatusPanel = QFrame(self.summaryCard)
        self.summaryStatusPanel.setObjectName(u"summaryStatusPanel")
        self.summaryStatusPanel.setFrameShape(QFrame.StyledPanel)
        self.summaryStatusLayout = QHBoxLayout(self.summaryStatusPanel)
        self.summaryStatusLayout.setSpacing(14)
        self.summaryStatusLayout.setObjectName(u"summaryStatusLayout")
        self.summaryStatusLayout.setContentsMargins(14, 14, 14, 14)
        self.summaryStatusBadge = QLabel(self.summaryStatusPanel)
        self.summaryStatusBadge.setObjectName(u"summaryStatusBadge")
        self.summaryStatusBadge.setAlignment(Qt.AlignCenter)

        self.summaryStatusLayout.addWidget(self.summaryStatusBadge)

        self.summaryStatusTextLayout = QVBoxLayout()
        self.summaryStatusTextLayout.setSpacing(2)
        self.summaryStatusTextLayout.setObjectName(u"summaryStatusTextLayout")
        self.summaryStatusTitle = QLabel(self.summaryStatusPanel)
        self.summaryStatusTitle.setObjectName(u"summaryStatusTitle")
        self.summaryStatusTitle.setWordWrap(True)

        self.summaryStatusTextLayout.addWidget(self.summaryStatusTitle)

        self.summaryStatusHint = QLabel(self.summaryStatusPanel)
        self.summaryStatusHint.setObjectName(u"summaryStatusHint")
        self.summaryStatusHint.setWordWrap(True)

        self.summaryStatusTextLayout.addWidget(self.summaryStatusHint)


        self.summaryStatusLayout.addLayout(self.summaryStatusTextLayout)


        self.summaryLayout.addWidget(self.summaryStatusPanel)

        self.summaryOutput = QLabel(self.summaryCard)
        self.summaryOutput.setObjectName(u"summaryOutput")
        self.summaryOutput.setWordWrap(True)
        self.summaryOutput.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.summaryLayout.addWidget(self.summaryOutput)


        self.rootLayout.addWidget(self.summaryCard)

        self.logCard = QFrame(generatePageForm)
        self.logCard.setObjectName(u"logCard")
        self.logCard.setFrameShape(QFrame.StyledPanel)
        self.logLayout = QVBoxLayout(self.logCard)
        self.logLayout.setSpacing(14)
        self.logLayout.setObjectName(u"logLayout")
        self.logLayout.setContentsMargins(20, 18, 20, 18)
        self.logTitleBar = QFrame(self.logCard)
        self.logTitleBar.setObjectName(u"logTitleBar")
        self.logTitleBar.setFrameShape(QFrame.NoFrame)
        self.logTitleLayout = QHBoxLayout(self.logTitleBar)
        self.logTitleLayout.setSpacing(12)
        self.logTitleLayout.setObjectName(u"logTitleLayout")
        self.logTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.logTitle = QLabel(self.logTitleBar)
        self.logTitle.setObjectName(u"logTitle")

        self.logTitleLayout.addWidget(self.logTitle)

        self.logTitleSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.logTitleLayout.addItem(self.logTitleSpacer)

        self.logStateBadge = QLabel(self.logTitleBar)
        self.logStateBadge.setObjectName(u"logStateBadge")
        self.logStateBadge.setAlignment(Qt.AlignCenter)

        self.logTitleLayout.addWidget(self.logStateBadge)


        self.logLayout.addWidget(self.logTitleBar)

        self.logOutput = QPlainTextEdit(self.logCard)
        self.logOutput.setObjectName(u"logOutput")
        self.logOutput.setMinimumSize(QSize(0, 220))

        self.logLayout.addWidget(self.logOutput)


        self.rootLayout.addWidget(self.logCard)

        self.actionRow = QHBoxLayout()
        self.actionRow.setSpacing(12)
        self.actionRow.setObjectName(u"actionRow")
        self.actionHint = QLabel(generatePageForm)
        self.actionHint.setObjectName(u"actionHint")
        self.actionHint.setWordWrap(True)

        self.actionRow.addWidget(self.actionHint)

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
        self.summaryStatusBadge.setText(QCoreApplication.translate("GeneratePageForm", u"READY", None))
        self.summaryStatusTitle.setText(QCoreApplication.translate("GeneratePageForm", u"Ready to generate documents.", None))
        self.summaryStatusHint.setText(QCoreApplication.translate("GeneratePageForm", u"Everything looks good. You can continue to generation.", None))
        self.summaryOutput.setText(QCoreApplication.translate("GeneratePageForm", u"Summary", None))
        self.logTitle.setText(QCoreApplication.translate("GeneratePageForm", u"Generation log", None))
        self.logStateBadge.setText(QCoreApplication.translate("GeneratePageForm", u"IDLE", None))
        self.actionHint.setText(QCoreApplication.translate("GeneratePageForm", u"Everything looks good. You can continue to generation.", None))
        self.generateButton.setText(QCoreApplication.translate("GeneratePageForm", u"Generate documents", None))
        pass
    # retranslateUi


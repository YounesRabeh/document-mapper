# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'results_page.ui'
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
from PySide6.QtWidgets import (QApplication, QGroupBox, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QVBoxLayout, QWidget)

class Ui_ResultsPageForm(object):
    def setupUi(self, resultsPageForm):
        if not resultsPageForm.objectName():
            resultsPageForm.setObjectName(u"resultsPageForm")
        self.rootLayout = QVBoxLayout(resultsPageForm)
        self.rootLayout.setSpacing(16)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.summaryLabel = QLabel(resultsPageForm)
        self.summaryLabel.setObjectName(u"summaryLabel")
        self.summaryLabel.setMinimumSize(QSize(0, 72))
        self.summaryLabel.setObjectName(u"workflowStatus")
        self.summaryLabel.setWordWrap(True)

        self.rootLayout.addWidget(self.summaryLabel)

        self.filesBox = QGroupBox(resultsPageForm)
        self.filesBox.setObjectName(u"filesBox")
        self.filesLayout = QVBoxLayout(self.filesBox)
        self.filesLayout.setObjectName(u"filesLayout")
        self.filesLayout.setContentsMargins(12, 12, 12, 12)
        self.filesList = QListWidget(self.filesBox)
        self.filesList.setObjectName(u"filesList")
        self.filesList.setMinimumSize(QSize(0, 150))

        self.filesLayout.addWidget(self.filesList)


        self.rootLayout.addWidget(self.filesBox)

        self.errorsBox = QGroupBox(resultsPageForm)
        self.errorsBox.setObjectName(u"errorsBox")
        self.errorsLayout = QVBoxLayout(self.errorsBox)
        self.errorsLayout.setObjectName(u"errorsLayout")
        self.errorsLayout.setContentsMargins(12, 12, 12, 12)
        self.errorsOutput = QPlainTextEdit(self.errorsBox)
        self.errorsOutput.setObjectName(u"errorsOutput")
        self.errorsOutput.setMinimumSize(QSize(0, 150))

        self.errorsLayout.addWidget(self.errorsOutput)


        self.rootLayout.addWidget(self.errorsBox)

        self.actionRow = QHBoxLayout()
        self.actionRow.setObjectName(u"actionRow")
        self.actionStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionRow.addItem(self.actionStretch)

        self.openLogButton = QPushButton(resultsPageForm)
        self.openLogButton.setObjectName(u"openLogButton")

        self.actionRow.addWidget(self.openLogButton)

        self.openOutputButton = QPushButton(resultsPageForm)
        self.openOutputButton.setObjectName(u"openOutputButton")

        self.actionRow.addWidget(self.openOutputButton)


        self.rootLayout.addLayout(self.actionRow)


        self.retranslateUi(resultsPageForm)

        QMetaObject.connectSlotsByName(resultsPageForm)
    # setupUi

    def retranslateUi(self, resultsPageForm):
        self.summaryLabel.setText(QCoreApplication.translate("ResultsPageForm", u"Summary", None))
        self.filesBox.setTitle(QCoreApplication.translate("ResultsPageForm", u"Generated files", None))
        self.errorsBox.setTitle(QCoreApplication.translate("ResultsPageForm", u"Errors", None))
        self.openLogButton.setText(QCoreApplication.translate("ResultsPageForm", u"Open log", None))
        self.openOutputButton.setText(QCoreApplication.translate("ResultsPageForm", u"Open output folder", None))
        pass
    # retranslateUi


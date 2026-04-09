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
from PySide6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
    QPlainTextEdit, QPushButton, QSizePolicy, QSpacerItem,
    QSplitter, QStackedWidget, QVBoxLayout, QWidget)

class Ui_ResultsPageForm(object):
    def setupUi(self, resultsPageForm):
        if not resultsPageForm.objectName():
            resultsPageForm.setObjectName(u"resultsPageForm")
        self.rootLayout = QVBoxLayout(resultsPageForm)
        self.rootLayout.setSpacing(18)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.resultsSummaryCard = QFrame(resultsPageForm)
        self.resultsSummaryCard.setObjectName(u"resultsSummaryCard")
        self.resultsSummaryCard.setFrameShape(QFrame.StyledPanel)
        self.summaryLayout = QVBoxLayout(self.resultsSummaryCard)
        self.summaryLayout.setSpacing(14)
        self.summaryLayout.setObjectName(u"summaryLayout")
        self.summaryLayout.setContentsMargins(20, 18, 20, 18)
        self.summaryTitleBar = QFrame(self.resultsSummaryCard)
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

        self.resultsStatusPanel = QFrame(self.resultsSummaryCard)
        self.resultsStatusPanel.setObjectName(u"resultsStatusPanel")
        self.resultsStatusPanel.setFrameShape(QFrame.StyledPanel)
        self.resultsStatusLayout = QHBoxLayout(self.resultsStatusPanel)
        self.resultsStatusLayout.setSpacing(14)
        self.resultsStatusLayout.setObjectName(u"resultsStatusLayout")
        self.resultsStatusLayout.setContentsMargins(14, 14, 14, 14)
        self.resultsStatusBadge = QLabel(self.resultsStatusPanel)
        self.resultsStatusBadge.setObjectName(u"resultsStatusBadge")
        self.resultsStatusBadge.setAlignment(Qt.AlignCenter)

        self.resultsStatusLayout.addWidget(self.resultsStatusBadge)

        self.resultsStatusTextLayout = QVBoxLayout()
        self.resultsStatusTextLayout.setSpacing(2)
        self.resultsStatusTextLayout.setObjectName(u"resultsStatusTextLayout")
        self.resultsStatusTitle = QLabel(self.resultsStatusPanel)
        self.resultsStatusTitle.setObjectName(u"resultsStatusTitle")
        self.resultsStatusTitle.setWordWrap(True)

        self.resultsStatusTextLayout.addWidget(self.resultsStatusTitle)

        self.resultsStatusHint = QLabel(self.resultsStatusPanel)
        self.resultsStatusHint.setObjectName(u"resultsStatusHint")
        self.resultsStatusHint.setWordWrap(True)

        self.resultsStatusTextLayout.addWidget(self.resultsStatusHint)


        self.resultsStatusLayout.addLayout(self.resultsStatusTextLayout)


        self.summaryLayout.addWidget(self.resultsStatusPanel)

        self.summaryLabel = QLabel(self.resultsSummaryCard)
        self.summaryLabel.setObjectName(u"summaryLabel")
        self.summaryLabel.setMinimumSize(QSize(0, 120))
        self.summaryLabel.setWordWrap(True)
        self.summaryLabel.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)

        self.summaryLayout.addWidget(self.summaryLabel)


        self.rootLayout.addWidget(self.resultsSummaryCard)

        self.filesCard = QFrame(resultsPageForm)
        self.filesCard.setObjectName(u"filesCard")
        self.filesCard.setFrameShape(QFrame.StyledPanel)
        self.filesCardLayout = QVBoxLayout(self.filesCard)
        self.filesCardLayout.setSpacing(14)
        self.filesCardLayout.setObjectName(u"filesCardLayout")
        self.filesCardLayout.setContentsMargins(20, 18, 20, 18)
        self.filesHeader = QFrame(self.filesCard)
        self.filesHeader.setObjectName(u"filesHeader")
        self.filesHeader.setFrameShape(QFrame.NoFrame)
        self.filesHeaderLayout = QHBoxLayout(self.filesHeader)
        self.filesHeaderLayout.setSpacing(12)
        self.filesHeaderLayout.setObjectName(u"filesHeaderLayout")
        self.filesHeaderLayout.setContentsMargins(0, 0, 0, 0)
        self.filesTitle = QLabel(self.filesHeader)
        self.filesTitle.setObjectName(u"filesTitle")

        self.filesHeaderLayout.addWidget(self.filesTitle)

        self.filesHeaderSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.filesHeaderLayout.addItem(self.filesHeaderSpacer)

        self.filesCountBadge = QLabel(self.filesHeader)
        self.filesCountBadge.setObjectName(u"filesCountBadge")
        self.filesCountBadge.setAlignment(Qt.AlignCenter)

        self.filesHeaderLayout.addWidget(self.filesCountBadge)


        self.filesCardLayout.addWidget(self.filesHeader)

        self.filesViewStack = QStackedWidget(self.filesCard)
        self.filesViewStack.setObjectName(u"filesViewStack")
        self.singleFilesPage = QWidget()
        self.singleFilesPage.setObjectName(u"singleFilesPage")
        self.singleFilesPageLayout = QVBoxLayout(self.singleFilesPage)
        self.singleFilesPageLayout.setSpacing(0)
        self.singleFilesPageLayout.setObjectName(u"singleFilesPageLayout")
        self.singleFilesPageLayout.setContentsMargins(0, 0, 0, 0)
        self.singleFilesContainer = QWidget(self.singleFilesPage)
        self.singleFilesContainer.setObjectName(u"singleFilesContainer")

        self.singleFilesPageLayout.addWidget(self.singleFilesContainer)

        self.filesViewStack.addWidget(self.singleFilesPage)
        self.splitFilesPage = QWidget()
        self.splitFilesPage.setObjectName(u"splitFilesPage")
        self.splitFilesPageLayout = QVBoxLayout(self.splitFilesPage)
        self.splitFilesPageLayout.setSpacing(0)
        self.splitFilesPageLayout.setObjectName(u"splitFilesPageLayout")
        self.splitFilesPageLayout.setContentsMargins(0, 0, 0, 0)
        self.filesSplitView = QSplitter(self.splitFilesPage)
        self.filesSplitView.setObjectName(u"filesSplitView")
        self.filesSplitView.setOrientation(Qt.Vertical)
        self.docxFilesContainer = QFrame(self.filesSplitView)
        self.docxFilesContainer.setObjectName(u"docxFilesContainer")
        self.docxFilesContainer.setFrameShape(QFrame.NoFrame)
        self.docxFilesContainerLayout = QVBoxLayout(self.docxFilesContainer)
        self.docxFilesContainerLayout.setSpacing(0)
        self.docxFilesContainerLayout.setObjectName(u"docxFilesContainerLayout")
        self.docxFilesContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.filesSplitView.addWidget(self.docxFilesContainer)
        self.pdfFilesContainer = QFrame(self.filesSplitView)
        self.pdfFilesContainer.setObjectName(u"pdfFilesContainer")
        self.pdfFilesContainer.setFrameShape(QFrame.NoFrame)
        self.pdfFilesContainerLayout = QVBoxLayout(self.pdfFilesContainer)
        self.pdfFilesContainerLayout.setSpacing(0)
        self.pdfFilesContainerLayout.setObjectName(u"pdfFilesContainerLayout")
        self.pdfFilesContainerLayout.setContentsMargins(0, 0, 0, 0)
        self.filesSplitView.addWidget(self.pdfFilesContainer)

        self.splitFilesPageLayout.addWidget(self.filesSplitView)

        self.filesViewStack.addWidget(self.splitFilesPage)

        self.filesCardLayout.addWidget(self.filesViewStack)


        self.rootLayout.addWidget(self.filesCard)

        self.errorsCard = QFrame(resultsPageForm)
        self.errorsCard.setObjectName(u"errorsCard")
        self.errorsCard.setFrameShape(QFrame.StyledPanel)
        self.errorsCardLayout = QVBoxLayout(self.errorsCard)
        self.errorsCardLayout.setSpacing(14)
        self.errorsCardLayout.setObjectName(u"errorsCardLayout")
        self.errorsCardLayout.setContentsMargins(20, 18, 20, 18)
        self.errorsHeader = QFrame(self.errorsCard)
        self.errorsHeader.setObjectName(u"errorsHeader")
        self.errorsHeader.setFrameShape(QFrame.NoFrame)
        self.errorsHeaderLayout = QHBoxLayout(self.errorsHeader)
        self.errorsHeaderLayout.setSpacing(12)
        self.errorsHeaderLayout.setObjectName(u"errorsHeaderLayout")
        self.errorsHeaderLayout.setContentsMargins(0, 0, 0, 0)
        self.errorsTitle = QLabel(self.errorsHeader)
        self.errorsTitle.setObjectName(u"errorsTitle")

        self.errorsHeaderLayout.addWidget(self.errorsTitle)

        self.errorsHeaderSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.errorsHeaderLayout.addItem(self.errorsHeaderSpacer)

        self.errorsCountBadge = QLabel(self.errorsHeader)
        self.errorsCountBadge.setObjectName(u"errorsCountBadge")
        self.errorsCountBadge.setAlignment(Qt.AlignCenter)

        self.errorsHeaderLayout.addWidget(self.errorsCountBadge)


        self.errorsCardLayout.addWidget(self.errorsHeader)

        self.errorsOutput = QPlainTextEdit(self.errorsCard)
        self.errorsOutput.setObjectName(u"errorsOutput")
        self.errorsOutput.setMinimumSize(QSize(0, 150))

        self.errorsCardLayout.addWidget(self.errorsOutput)


        self.rootLayout.addWidget(self.errorsCard)

        self.actionsLayout = QVBoxLayout()
        self.actionsLayout.setSpacing(10)
        self.actionsLayout.setObjectName(u"actionsLayout")
        self.actionRow = QHBoxLayout()
        self.actionRow.setSpacing(12)
        self.actionRow.setObjectName(u"actionRow")
        self.actionHint = QLabel(resultsPageForm)
        self.actionHint.setObjectName(u"actionHint")
        self.actionHint.setWordWrap(True)

        self.actionRow.addWidget(self.actionHint)

        self.actionStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.actionRow.addItem(self.actionStretch)

        self.openLogButton = QPushButton(resultsPageForm)
        self.openLogButton.setObjectName(u"openLogButton")

        self.actionRow.addWidget(self.openLogButton)

        self.openOutputButton = QPushButton(resultsPageForm)
        self.openOutputButton.setObjectName(u"openOutputButton")

        self.actionRow.addWidget(self.openOutputButton)


        self.actionsLayout.addLayout(self.actionRow)


        self.rootLayout.addLayout(self.actionsLayout)


        self.retranslateUi(resultsPageForm)

        self.filesViewStack.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(resultsPageForm)
    # setupUi

    def retranslateUi(self, resultsPageForm):
        self.summaryTitle.setText(QCoreApplication.translate("ResultsPageForm", u"Run summary", None))
        self.resultsStatusBadge.setText(QCoreApplication.translate("ResultsPageForm", u"COMPLETE", None))
        self.resultsStatusTitle.setText(QCoreApplication.translate("ResultsPageForm", u"Batch completed successfully.", None))
        self.resultsStatusHint.setText(QCoreApplication.translate("ResultsPageForm", u"Your documents are ready. Open a file below or jump straight to the output folder.", None))
        self.summaryLabel.setText(QCoreApplication.translate("ResultsPageForm", u"Summary", None))
        self.filesTitle.setText(QCoreApplication.translate("ResultsPageForm", u"Generated files", None))
        self.filesCountBadge.setText(QCoreApplication.translate("ResultsPageForm", u"0", None))
        self.errorsTitle.setText(QCoreApplication.translate("ResultsPageForm", u"Errors", None))
        self.errorsCountBadge.setText(QCoreApplication.translate("ResultsPageForm", u"0", None))
        self.actionHint.setText(QCoreApplication.translate("ResultsPageForm", u"Use Open on any generated file to launch it instantly.", None))
        self.openLogButton.setText(QCoreApplication.translate("ResultsPageForm", u"Open log", None))
        self.openOutputButton.setText(QCoreApplication.translate("ResultsPageForm", u"Open output folder", None))
        pass
    # retranslateUi


# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mapping_page.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QSizePolicy, QSpacerItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget)

from gui.workflow.base import TokenSuggestingLineEdit

class Ui_MappingPageForm(object):
    def setupUi(self, mappingPageForm):
        if not mappingPageForm.objectName():
            mappingPageForm.setObjectName(u"mappingPageForm")
        self.contentLayout = QHBoxLayout(mappingPageForm)
        self.contentLayout.setSpacing(16)
        self.contentLayout.setObjectName(u"contentLayout")
        self.contentLayout.setContentsMargins(0, 0, 0, 0)
        self.leftBox = QFrame(mappingPageForm)
        self.leftBox.setObjectName(u"leftBox")
        self.leftBox.setMinimumSize(QSize(260, 230))
        self.leftBox.setFrameShape(QFrame.StyledPanel)
        self.leftBox.setObjectName(u"workflowCard")
        self.leftBoxLayout = QVBoxLayout(self.leftBox)
        self.leftBoxLayout.setSpacing(14)
        self.leftBoxLayout.setObjectName(u"leftBoxLayout")
        self.leftBoxLayout.setContentsMargins(18, 16, 18, 16)
        self.leftTitleBar = QFrame(self.leftBox)
        self.leftTitleBar.setObjectName(u"leftTitleBar")
        self.leftTitleBar.setFrameShape(QFrame.NoFrame)
        self.leftTitleBar.setObjectName(u"workflowCardTitleBar")
        self.leftTitleLayout = QHBoxLayout(self.leftTitleBar)
        self.leftTitleLayout.setSpacing(0)
        self.leftTitleLayout.setObjectName(u"leftTitleLayout")
        self.leftTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.leftTitle = QLabel(self.leftTitleBar)
        self.leftTitle.setObjectName(u"leftTitle")
        self.leftTitle.setObjectName(u"workflowCardTitle")

        self.leftTitleLayout.addWidget(self.leftTitle)


        self.leftBoxLayout.addWidget(self.leftTitleBar)

        self.columnsLabel = QLabel(self.leftBox)
        self.columnsLabel.setObjectName(u"columnsLabel")
        self.columnsLabel.setObjectName(u"workflowStatus")
        self.columnsLabel.setWordWrap(True)

        self.leftBoxLayout.addWidget(self.columnsLabel)

        self.columnsHint = QLabel(self.leftBox)
        self.columnsHint.setObjectName(u"columnsHint")
        self.columnsHint.setObjectName(u"workflowHint")
        self.columnsHint.setWordWrap(True)

        self.leftBoxLayout.addWidget(self.columnsHint)

        self.columnsList = QListWidget(self.leftBox)
        self.columnsList.setObjectName(u"columnsList")

        self.leftBoxLayout.addWidget(self.columnsList)


        self.contentLayout.addWidget(self.leftBox)

        self.rightBox = QFrame(mappingPageForm)
        self.rightBox.setObjectName(u"rightBox")
        self.rightBox.setMinimumSize(QSize(420, 0))
        self.rightBox.setFrameShape(QFrame.StyledPanel)
        self.rightBox.setObjectName(u"workflowCard")
        self.rightBoxLayout = QVBoxLayout(self.rightBox)
        self.rightBoxLayout.setSpacing(14)
        self.rightBoxLayout.setObjectName(u"rightBoxLayout")
        self.rightBoxLayout.setContentsMargins(18, 16, 18, 16)
        self.rightTitleBar = QFrame(self.rightBox)
        self.rightTitleBar.setObjectName(u"rightTitleBar")
        self.rightTitleBar.setFrameShape(QFrame.NoFrame)
        self.rightTitleBar.setObjectName(u"workflowCardTitleBar")
        self.rightTitleLayout = QHBoxLayout(self.rightTitleBar)
        self.rightTitleLayout.setSpacing(0)
        self.rightTitleLayout.setObjectName(u"rightTitleLayout")
        self.rightTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.rightTitle = QLabel(self.rightTitleBar)
        self.rightTitle.setObjectName(u"rightTitle")
        self.rightTitle.setObjectName(u"workflowCardTitle")

        self.rightTitleLayout.addWidget(self.rightTitle)


        self.rightBoxLayout.addWidget(self.rightTitleBar)

        self.mappingHint = QLabel(self.rightBox)
        self.mappingHint.setObjectName(u"mappingHint")
        self.mappingHint.setObjectName(u"workflowHint")
        self.mappingHint.setWordWrap(True)

        self.rightBoxLayout.addWidget(self.mappingHint)

        self.delimiterRow = QHBoxLayout()
        self.delimiterRow.setSpacing(12)
        self.delimiterRow.setObjectName(u"delimiterRow")
        self.delimiterLabel = QLabel(self.rightBox)
        self.delimiterLabel.setObjectName(u"delimiterLabel")
        self.delimiterLabel.setObjectName(u"workflowFieldLabel")

        self.delimiterRow.addWidget(self.delimiterLabel)

        self.delimiterInput = QLineEdit(self.rightBox)
        self.delimiterInput.setObjectName(u"delimiterInput")
        self.delimiterInput.setMaximumSize(QSize(220, 16777215))
        self.delimiterInput.setMinimumSize(QSize(0, 40))
        self.delimiterInput.setClearButtonEnabled(True)

        self.delimiterRow.addWidget(self.delimiterInput)

        self.delimiterStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.delimiterRow.addItem(self.delimiterStretch)


        self.rightBoxLayout.addLayout(self.delimiterRow)

        self.templateStatus = QLabel(self.rightBox)
        self.templateStatus.setObjectName(u"templateStatus")
        self.templateStatus.setObjectName(u"workflowStatus")
        self.templateStatus.setWordWrap(True)

        self.rightBoxLayout.addWidget(self.templateStatus)

        self.outputNamingGroup = QGroupBox(self.rightBox)
        self.outputNamingGroup.setObjectName(u"outputNamingGroup")
        self.outputNamingLayout = QGridLayout(self.outputNamingGroup)
        self.outputNamingLayout.setObjectName(u"outputNamingLayout")
        self.outputNamingLayout.setHorizontalSpacing(12)
        self.outputNamingLayout.setVerticalSpacing(10)
        self.outputNamingLayout.setContentsMargins(16, 18, 16, 16)
        self.outputNamingSchemaLabel = QLabel(self.outputNamingGroup)
        self.outputNamingSchemaLabel.setObjectName(u"outputNamingSchemaLabel")
        self.outputNamingSchemaLabel.setObjectName(u"workflowFieldLabel")

        self.outputNamingLayout.addWidget(self.outputNamingSchemaLabel, 0, 0, 1, 1)

        self.outputNamingSchemaInput = TokenSuggestingLineEdit(self.outputNamingGroup)
        self.outputNamingSchemaInput.setObjectName(u"outputNamingSchemaInput")

        self.outputNamingLayout.addWidget(self.outputNamingSchemaInput, 0, 1, 1, 1)

        self.outputNamingSchemaHint = QLabel(self.outputNamingGroup)
        self.outputNamingSchemaHint.setObjectName(u"outputNamingSchemaHint")
        self.outputNamingSchemaHint.setObjectName(u"workflowHint")
        self.outputNamingSchemaHint.setWordWrap(True)

        self.outputNamingLayout.addWidget(self.outputNamingSchemaHint, 1, 1, 1, 1)


        self.rightBoxLayout.addWidget(self.outputNamingGroup)

        self.mappingButtonsLayout = QHBoxLayout()
        self.mappingButtonsLayout.setObjectName(u"mappingButtonsLayout")
        self.addButton = QPushButton(self.rightBox)
        self.addButton.setObjectName(u"addButton")

        self.mappingButtonsLayout.addWidget(self.addButton)

        self.refreshButton = QPushButton(self.rightBox)
        self.refreshButton.setObjectName(u"refreshButton")

        self.mappingButtonsLayout.addWidget(self.refreshButton)

        self.mappingButtonsStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.mappingButtonsLayout.addItem(self.mappingButtonsStretch)


        self.rightBoxLayout.addLayout(self.mappingButtonsLayout)

        self.mappingTable = QTableWidget(self.rightBox)
        if (self.mappingTable.columnCount() < 2):
            self.mappingTable.setColumnCount(2)
        __qtablewidgetitem = QTableWidgetItem()
        self.mappingTable.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.mappingTable.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        self.mappingTable.setObjectName(u"mappingTable")
        self.mappingTable.setMinimumSize(QSize(0, 300))

        self.rightBoxLayout.addWidget(self.mappingTable)

        self.validationLabel = QLabel(self.rightBox)
        self.validationLabel.setObjectName(u"validationLabel")
        self.validationLabel.setObjectName(u"workflowFieldLabel")

        self.rightBoxLayout.addWidget(self.validationLabel)

        self.validationSummary = QLabel(self.rightBox)
        self.validationSummary.setObjectName(u"validationSummary")
        self.validationSummary.setObjectName(u"workflowStatus")
        self.validationSummary.setWordWrap(True)

        self.rightBoxLayout.addWidget(self.validationSummary)

        self.validationOutput = QPlainTextEdit(self.rightBox)
        self.validationOutput.setObjectName(u"validationOutput")
        self.validationOutput.setMinimumSize(QSize(0, 160))

        self.rightBoxLayout.addWidget(self.validationOutput)


        self.contentLayout.addWidget(self.rightBox)


        self.retranslateUi(mappingPageForm)

        QMetaObject.connectSlotsByName(mappingPageForm)
    # setupUi

    def retranslateUi(self, mappingPageForm):
        self.leftTitle.setText(QCoreApplication.translate("MappingPageForm", u"Workbook columns", None))
        self.columnsLabel.setText(QCoreApplication.translate("MappingPageForm", u"No workbook loaded", None))
        self.columnsHint.setText(QCoreApplication.translate("MappingPageForm", u"Hint", None))
        self.rightTitle.setText(QCoreApplication.translate("MappingPageForm", u"Placeholder mappings", None))
        self.mappingHint.setText(QCoreApplication.translate("MappingPageForm", u"Hint", None))
        self.delimiterLabel.setText(QCoreApplication.translate("MappingPageForm", u"Delimiter", None))
        self.templateStatus.setText(QCoreApplication.translate("MappingPageForm", u"Status", None))
        self.outputNamingGroup.setTitle(QCoreApplication.translate("MappingPageForm", u"Output naming schema", None))
        self.outputNamingSchemaLabel.setText(QCoreApplication.translate("MappingPageForm", u"Output naming schema", None))
        self.outputNamingSchemaHint.setText(QCoreApplication.translate("MappingPageForm", u"Hint", None))
        self.addButton.setText(QCoreApplication.translate("MappingPageForm", u"Add mapping", None))
        self.refreshButton.setText(QCoreApplication.translate("MappingPageForm", u"Refresh", None))
        ___qtablewidgetitem = self.mappingTable.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("MappingPageForm", u"Placeholder", None))
        ___qtablewidgetitem1 = self.mappingTable.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("MappingPageForm", u"Excel column", None))
        self.validationLabel.setText(QCoreApplication.translate("MappingPageForm", u"Validation", None))
        self.validationSummary.setText(QCoreApplication.translate("MappingPageForm", u"Status", None))
        pass
    # retranslateUi


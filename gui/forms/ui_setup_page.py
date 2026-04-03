# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'setup_page.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpacerItem, QSpinBox, QVBoxLayout,
    QWidget)

class Ui_SetupPageForm(object):
    def setupUi(self, setupPageForm):
        if not setupPageForm.objectName():
            setupPageForm.setObjectName(u"setupPageForm")
        self.rootLayout = QVBoxLayout(setupPageForm)
        self.rootLayout.setSpacing(16)
        self.rootLayout.setObjectName(u"rootLayout")
        self.rootLayout.setContentsMargins(0, 0, 0, 0)
        self.formCard = QFrame(setupPageForm)
        self.formCard.setObjectName(u"formCard")
        self.formCard.setFrameShape(QFrame.StyledPanel)
        self.formCard.setObjectName(u"workflowCard")
        self.formCardLayout = QVBoxLayout(self.formCard)
        self.formCardLayout.setSpacing(14)
        self.formCardLayout.setObjectName(u"formCardLayout")
        self.formCardLayout.setContentsMargins(18, 16, 18, 16)
        self.formCardTitleBar = QFrame(self.formCard)
        self.formCardTitleBar.setObjectName(u"formCardTitleBar")
        self.formCardTitleBar.setFrameShape(QFrame.NoFrame)
        self.formCardTitleBar.setObjectName(u"workflowCardTitleBar")
        self.formCardTitleLayout = QHBoxLayout(self.formCardTitleBar)
        self.formCardTitleLayout.setSpacing(0)
        self.formCardTitleLayout.setObjectName(u"formCardTitleLayout")
        self.formCardTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.formCardTitle = QLabel(self.formCardTitleBar)
        self.formCardTitle.setObjectName(u"formCardTitle")
        self.formCardTitle.setObjectName(u"workflowCardTitle")

        self.formCardTitleLayout.addWidget(self.formCardTitle)


        self.formCardLayout.addWidget(self.formCardTitleBar)

        self.formLayout = QGridLayout()
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setHorizontalSpacing(16)
        self.formLayout.setVerticalSpacing(12)
        self.excelLabel = QLabel(self.formCard)
        self.excelLabel.setObjectName(u"excelLabel")
        self.excelLabel.setObjectName(u"workflowFieldLabel")

        self.formLayout.addWidget(self.excelLabel, 0, 0, 1, 1)

        self.excelInputContainer = QWidget(self.formCard)
        self.excelInputContainer.setObjectName(u"excelInputContainer")
        self.excelInputLayout = QHBoxLayout(self.excelInputContainer)
        self.excelInputLayout.setSpacing(0)
        self.excelInputLayout.setObjectName(u"excelInputLayout")
        self.excelInputLayout.setContentsMargins(0, 0, 0, 0)
        self.excelLineEdit = QLineEdit(self.excelInputContainer)
        self.excelLineEdit.setObjectName(u"excelLineEdit")
        self.excelLineEdit.setMinimumSize(QSize(360, 40))
        self.excelLineEdit.setClearButtonEnabled(True)

        self.excelInputLayout.addWidget(self.excelLineEdit)


        self.formLayout.addWidget(self.excelInputContainer, 0, 1, 1, 1)

        self.excelBrowseButton = QPushButton(self.formCard)
        self.excelBrowseButton.setObjectName(u"excelBrowseButton")
        self.excelBrowseButton.setMinimumSize(QSize(148, 40))

        self.formLayout.addWidget(self.excelBrowseButton, 0, 2, 1, 1)

        self.outputLabel = QLabel(self.formCard)
        self.outputLabel.setObjectName(u"outputLabel")
        self.outputLabel.setObjectName(u"workflowFieldLabel")

        self.formLayout.addWidget(self.outputLabel, 1, 0, 1, 1)

        self.outputInputContainer = QWidget(self.formCard)
        self.outputInputContainer.setObjectName(u"outputInputContainer")
        self.outputInputLayout = QHBoxLayout(self.outputInputContainer)
        self.outputInputLayout.setSpacing(0)
        self.outputInputLayout.setObjectName(u"outputInputLayout")
        self.outputInputLayout.setContentsMargins(0, 0, 0, 0)
        self.outputLineEdit = QLineEdit(self.outputInputContainer)
        self.outputLineEdit.setObjectName(u"outputLineEdit")
        self.outputLineEdit.setMinimumSize(QSize(360, 40))
        self.outputLineEdit.setClearButtonEnabled(True)

        self.outputInputLayout.addWidget(self.outputLineEdit)


        self.formLayout.addWidget(self.outputInputContainer, 1, 1, 1, 1)

        self.outputBrowseButton = QPushButton(self.formCard)
        self.outputBrowseButton.setObjectName(u"outputBrowseButton")
        self.outputBrowseButton.setMinimumSize(QSize(148, 40))

        self.formLayout.addWidget(self.outputBrowseButton, 1, 2, 1, 1)


        self.formCardLayout.addLayout(self.formLayout)


        self.rootLayout.addWidget(self.formCard)

        self.templateOverrideCard = QFrame(setupPageForm)
        self.templateOverrideCard.setObjectName(u"templateOverrideCard")
        self.templateOverrideCard.setFrameShape(QFrame.StyledPanel)
        self.templateOverrideCard.setObjectName(u"workflowCard")
        self.templateOverrideCardLayout = QVBoxLayout(self.templateOverrideCard)
        self.templateOverrideCardLayout.setSpacing(14)
        self.templateOverrideCardLayout.setObjectName(u"templateOverrideCardLayout")
        self.templateOverrideCardLayout.setContentsMargins(18, 16, 18, 16)
        self.templateOverrideTitleBar = QFrame(self.templateOverrideCard)
        self.templateOverrideTitleBar.setObjectName(u"templateOverrideTitleBar")
        self.templateOverrideTitleBar.setFrameShape(QFrame.NoFrame)
        self.templateOverrideTitleBar.setObjectName(u"workflowCardTitleBar")
        self.templateOverrideTitleLayout = QHBoxLayout(self.templateOverrideTitleBar)
        self.templateOverrideTitleLayout.setSpacing(0)
        self.templateOverrideTitleLayout.setObjectName(u"templateOverrideTitleLayout")
        self.templateOverrideTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.templateOverrideTitle = QLabel(self.templateOverrideTitleBar)
        self.templateOverrideTitle.setObjectName(u"templateOverrideTitle")
        self.templateOverrideTitle.setObjectName(u"workflowCardTitle")

        self.templateOverrideTitleLayout.addWidget(self.templateOverrideTitle)


        self.templateOverrideCardLayout.addWidget(self.templateOverrideTitleBar)

        self.templateOverrideFormLayout = QGridLayout()
        self.templateOverrideFormLayout.setObjectName(u"templateOverrideFormLayout")
        self.templateOverrideFormLayout.setHorizontalSpacing(16)
        self.templateOverrideFormLayout.setVerticalSpacing(10)
        self.templateOverrideLabel = QLabel(self.templateOverrideCard)
        self.templateOverrideLabel.setObjectName(u"templateOverrideLabel")
        self.templateOverrideLabel.setObjectName(u"workflowFieldLabel")

        self.templateOverrideFormLayout.addWidget(self.templateOverrideLabel, 0, 0, 1, 1)

        self.templateOverrideInputContainer = QWidget(self.templateOverrideCard)
        self.templateOverrideInputContainer.setObjectName(u"templateOverrideInputContainer")
        self.templateOverrideInputLayout = QHBoxLayout(self.templateOverrideInputContainer)
        self.templateOverrideInputLayout.setSpacing(0)
        self.templateOverrideInputLayout.setObjectName(u"templateOverrideInputLayout")
        self.templateOverrideInputLayout.setContentsMargins(0, 0, 0, 0)
        self.templateOverrideLineEdit = QLineEdit(self.templateOverrideInputContainer)
        self.templateOverrideLineEdit.setObjectName(u"templateOverrideLineEdit")
        self.templateOverrideLineEdit.setMinimumSize(QSize(360, 40))
        self.templateOverrideLineEdit.setClearButtonEnabled(True)

        self.templateOverrideInputLayout.addWidget(self.templateOverrideLineEdit)


        self.templateOverrideFormLayout.addWidget(self.templateOverrideInputContainer, 0, 1, 1, 1)

        self.templateOverrideActions = QWidget(self.templateOverrideCard)
        self.templateOverrideActions.setObjectName(u"templateOverrideActions")
        self.templateOverrideActionsLayout = QHBoxLayout(self.templateOverrideActions)
        self.templateOverrideActionsLayout.setSpacing(8)
        self.templateOverrideActionsLayout.setObjectName(u"templateOverrideActionsLayout")
        self.templateOverrideActionsLayout.setContentsMargins(0, 0, 0, 0)
        self.templateOverrideBrowseButton = QPushButton(self.templateOverrideActions)
        self.templateOverrideBrowseButton.setObjectName(u"templateOverrideBrowseButton")
        self.templateOverrideBrowseButton.setMinimumSize(QSize(148, 40))

        self.templateOverrideActionsLayout.addWidget(self.templateOverrideBrowseButton)

        self.clearOverrideButton = QPushButton(self.templateOverrideActions)
        self.clearOverrideButton.setObjectName(u"clearOverrideButton")
        self.clearOverrideButton.setMinimumSize(QSize(110, 40))

        self.templateOverrideActionsLayout.addWidget(self.clearOverrideButton)


        self.templateOverrideFormLayout.addWidget(self.templateOverrideActions, 0, 2, 1, 1)

        self.templateOverrideHint = QLabel(self.templateOverrideCard)
        self.templateOverrideHint.setObjectName(u"templateOverrideHint")
        self.templateOverrideHint.setObjectName(u"workflowHint")
        self.templateOverrideHint.setWordWrap(True)

        self.templateOverrideFormLayout.addWidget(self.templateOverrideHint, 1, 1, 1, 2)


        self.templateOverrideCardLayout.addLayout(self.templateOverrideFormLayout)


        self.rootLayout.addWidget(self.templateOverrideCard)

        self.optionsCard = QFrame(setupPageForm)
        self.optionsCard.setObjectName(u"optionsCard")
        self.optionsCard.setFrameShape(QFrame.StyledPanel)
        self.optionsCard.setObjectName(u"workflowCard")
        self.optionsCardLayout = QVBoxLayout(self.optionsCard)
        self.optionsCardLayout.setSpacing(14)
        self.optionsCardLayout.setObjectName(u"optionsCardLayout")
        self.optionsCardLayout.setContentsMargins(18, 16, 18, 16)
        self.optionsTitleBar = QFrame(self.optionsCard)
        self.optionsTitleBar.setObjectName(u"optionsTitleBar")
        self.optionsTitleBar.setFrameShape(QFrame.NoFrame)
        self.optionsTitleBar.setObjectName(u"workflowCardTitleBar")
        self.optionsTitleLayout = QHBoxLayout(self.optionsTitleBar)
        self.optionsTitleLayout.setSpacing(0)
        self.optionsTitleLayout.setObjectName(u"optionsTitleLayout")
        self.optionsTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.optionsTitle = QLabel(self.optionsTitleBar)
        self.optionsTitle.setObjectName(u"optionsTitle")
        self.optionsTitle.setObjectName(u"workflowCardTitle")

        self.optionsTitleLayout.addWidget(self.optionsTitle)


        self.optionsCardLayout.addWidget(self.optionsTitleBar)

        self.exportRow = QHBoxLayout()
        self.exportRow.setSpacing(12)
        self.exportRow.setObjectName(u"exportRow")
        self.exportPdfCheckBox = QCheckBox(self.optionsCard)
        self.exportPdfCheckBox.setObjectName(u"exportPdfCheckBox")

        self.exportRow.addWidget(self.exportPdfCheckBox)

        self.optionsStretch = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.exportRow.addItem(self.optionsStretch)

        self.pdfTimeoutLabel = QLabel(self.optionsCard)
        self.pdfTimeoutLabel.setObjectName(u"pdfTimeoutLabel")
        self.pdfTimeoutLabel.setObjectName(u"workflowFieldLabel")

        self.exportRow.addWidget(self.pdfTimeoutLabel)

        self.pdfTimeoutSpinBox = QSpinBox(self.optionsCard)
        self.pdfTimeoutSpinBox.setObjectName(u"pdfTimeoutSpinBox")
        self.pdfTimeoutSpinBox.setMinimumSize(QSize(128, 40))

        self.exportRow.addWidget(self.pdfTimeoutSpinBox)


        self.optionsCardLayout.addLayout(self.exportRow)


        self.rootLayout.addWidget(self.optionsCard)

        self.statusCard = QFrame(setupPageForm)
        self.statusCard.setObjectName(u"statusCard")
        self.statusCard.setFrameShape(QFrame.StyledPanel)
        self.statusCard.setObjectName(u"workflowCard")
        self.statusCardLayout = QVBoxLayout(self.statusCard)
        self.statusCardLayout.setSpacing(14)
        self.statusCardLayout.setObjectName(u"statusCardLayout")
        self.statusCardLayout.setContentsMargins(18, 16, 18, 16)
        self.statusTitleBar = QFrame(self.statusCard)
        self.statusTitleBar.setObjectName(u"statusTitleBar")
        self.statusTitleBar.setFrameShape(QFrame.NoFrame)
        self.statusTitleBar.setObjectName(u"workflowCardTitleBar")
        self.statusTitleLayout = QHBoxLayout(self.statusTitleBar)
        self.statusTitleLayout.setSpacing(0)
        self.statusTitleLayout.setObjectName(u"statusTitleLayout")
        self.statusTitleLayout.setContentsMargins(0, 0, 0, 0)
        self.statusTitle = QLabel(self.statusTitleBar)
        self.statusTitle.setObjectName(u"statusTitle")
        self.statusTitle.setObjectName(u"workflowCardTitle")

        self.statusTitleLayout.addWidget(self.statusTitle)


        self.statusCardLayout.addWidget(self.statusTitleBar)

        self.statusLabel = QLabel(self.statusCard)
        self.statusLabel.setObjectName(u"statusLabel")
        self.statusLabel.setObjectName(u"workflowStatus")
        self.statusLabel.setMinimumSize(QSize(0, 96))
        self.statusLabel.setWordWrap(True)

        self.statusCardLayout.addWidget(self.statusLabel)


        self.rootLayout.addWidget(self.statusCard)


        self.retranslateUi(setupPageForm)

        QMetaObject.connectSlotsByName(setupPageForm)
    # setupUi

    def retranslateUi(self, setupPageForm):
        self.formCardTitle.setText(QCoreApplication.translate("SetupPageForm", u"Project inputs", None))
        self.excelLabel.setText(QCoreApplication.translate("SetupPageForm", u"Excel workbook", None))
        self.excelBrowseButton.setText(QCoreApplication.translate("SetupPageForm", u"Workbook", None))
        self.outputLabel.setText(QCoreApplication.translate("SetupPageForm", u"Output folder", None))
        self.outputBrowseButton.setText(QCoreApplication.translate("SetupPageForm", u"Output folder", None))
        self.templateOverrideTitle.setText(QCoreApplication.translate("SetupPageForm", u"Use a one-time template", None))
        self.templateOverrideLabel.setText(QCoreApplication.translate("SetupPageForm", u"Use one-time template", None))
        self.templateOverrideBrowseButton.setText(QCoreApplication.translate("SetupPageForm", u"Template", None))
        self.clearOverrideButton.setText(QCoreApplication.translate("SetupPageForm", u"Clear one-time template", None))
        self.templateOverrideHint.setText(QCoreApplication.translate("SetupPageForm", u"Use an external Word template for this run only.", None))
        self.optionsTitle.setText(QCoreApplication.translate("SetupPageForm", u"Export options", None))
        self.exportPdfCheckBox.setText(QCoreApplication.translate("SetupPageForm", u"Also export PDF", None))
        self.pdfTimeoutLabel.setText(QCoreApplication.translate("SetupPageForm", u"PDF timeout", None))
        self.statusTitle.setText(QCoreApplication.translate("SetupPageForm", u"Session summary", None))
        self.statusLabel.setText(QCoreApplication.translate("SetupPageForm", u"Summary", None))
        pass
    # retranslateUi


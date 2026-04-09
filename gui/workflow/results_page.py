from __future__ import annotations

from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidgetItem,
    QListWidget,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.mapping.models import GenerationResult, ProjectSession
from core.manager.localization_manager import LocalizationManager
from core.util.system_info import open_path
from gui.forms import Ui_ResultsPageForm
from gui.workflow.base import PANEL_MIN_HEIGHT, WorkflowPage

FILES_LIST_MIN_HEIGHT = 140
FILES_LIST_MAX_HEIGHT = 260
FILE_ENTRY_ESTIMATED_HEIGHT = 56
FILES_LIST_VERTICAL_PADDING = 12


class ElidedLabel(QLabel):
    def __init__(self, text: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self._full_text = ""
        self.setWordWrap(False)
        self.setText(text)

    def setText(self, text: str):
        self._full_text = str(text)
        super().setText(self._elided_text())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        super().setText(self._elided_text())

    def _elided_text(self) -> str:
        if not self._full_text:
            return ""
        available_width = max(self.contentsRect().width(), 0)
        if available_width <= 0:
            return self._full_text
        return self.fontMetrics().elidedText(self._full_text, Qt.TextElideMode.ElideRight, available_width)


class ResultsFileEntry(QWidget):
    def __init__(self, *, file_name: str, open_label: str, path: str, on_open):
        super().__init__()
        self._path = path
        self._on_open = on_open
        self.setObjectName("resultsFileEntry")
        self.setMinimumHeight(52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 7, 18, 7)
        layout.setSpacing(10)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        self.name_label = ElidedLabel(file_name)
        self.name_label.setObjectName("resultsFileName")
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.name_label.setToolTip(file_name)
        text_layout.addWidget(self.name_label)
        self.setToolTip(path)

        layout.addLayout(text_layout, 1)

        self.open_button = QPushButton(open_label)
        self.open_button.setObjectName("resultsFileOpenButton")
        self.open_button.clicked.connect(self._handle_open)
        layout.addWidget(self.open_button, 0, Qt.AlignVCenter)

    def _handle_open(self):
        self._on_open(self._path)


class ResultsFilesPanel(QWidget):
    def __init__(
        self,
        *,
        list_object_name: str,
        badge_object_name: str,
        title_visible: bool = True,
    ):
        super().__init__()
        self.setObjectName("resultsFilesPanel")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignTop)

        self.header = QFrame()
        self.header.setObjectName("resultsFilesPanelHeader")
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        self.title_label = QLabel()
        self.title_label.setObjectName("workflowCardTitle")
        header_layout.addWidget(self.title_label)

        header_layout.addStretch(1)

        self.count_badge = QLabel("0")
        self.count_badge.setObjectName(badge_object_name)
        self.count_badge.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.count_badge)

        layout.addWidget(self.header)

        self.list_widget = QListWidget()
        self.list_widget.setObjectName(list_object_name)
        self.list_widget.setMinimumHeight(FILES_LIST_MIN_HEIGHT)
        self.list_widget.setMaximumHeight(FILES_LIST_MAX_HEIGHT)
        self.list_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        self.list_widget.setSpacing(4)
        self.list_widget.setSelectionMode(self.list_widget.SelectionMode.NoSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.list_widget)

        self.set_header_visible(title_visible)

    def set_header_visible(self, visible: bool):
        self.header.setVisible(visible)

    def populate_entries(self, *, paths: list[str], open_label: str, on_open, empty_text: str):
        self.list_widget.clear()
        for path in paths:
            item = QListWidgetItem()
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            entry = ResultsFileEntry(
                file_name=Path(path).name,
                open_label=open_label,
                path=path,
                on_open=on_open,
            )
            item.setSizeHint(entry.sizeHint())
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, entry)
        if self.list_widget.count() == 0:
            placeholder_item = QListWidgetItem(empty_text)
            placeholder_item.setFlags(Qt.NoItemFlags)
            self.list_widget.addItem(placeholder_item)
        self._adjust_list_height(self.list_widget.count())

    def _adjust_list_height(self, rows: int):
        desired_height = (max(rows, 1) * FILE_ENTRY_ESTIMATED_HEIGHT) + FILES_LIST_VERTICAL_PADDING
        clamped_height = max(FILES_LIST_MIN_HEIGHT, min(FILES_LIST_MAX_HEIGHT, desired_height))
        self.list_widget.setMinimumHeight(clamped_height)
        self.list_widget.setMaximumHeight(clamped_height)


class ResultsPage(WorkflowPage):
    def __init__(self, localization: LocalizationManager):
        super().__init__(
            localization,
            "page.results.title",
            "page.results.description",
        )
        self.result = GenerationResult()

        self.ui = Ui_ResultsPageForm()
        self.form_root = QWidget()
        self.ui.setupUi(self.form_root)
        self.form_root.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.ui.rootLayout.setSizeConstraint(self.ui.rootLayout.SizeConstraint.SetMinimumSize)
        self.ui.rootLayout.setAlignment(Qt.AlignTop)
        self.ui.filesCardLayout.setAlignment(Qt.AlignTop)
        self.ui.singleFilesPageLayout.setAlignment(Qt.AlignTop)
        self.ui.splitFilesPageLayout.setAlignment(Qt.AlignTop)
        self.body_layout.addWidget(self.form_root)

        self.summary_card = self.ui.resultsSummaryCard
        self.summary_title = self.ui.summaryTitle
        self.results_status_panel = self.ui.resultsStatusPanel
        self.results_status_badge = self.ui.resultsStatusBadge
        self.results_status_title = self.ui.resultsStatusTitle
        self.results_status_hint = self.ui.resultsStatusHint
        self.summary_label = self.ui.summaryLabel
        self.files_box = self.ui.filesCard
        self.files_title = self.ui.filesTitle
        self.files_count_badge = self.ui.filesCountBadge
        self.files_view_stack = self.ui.filesViewStack
        self.single_files_page = self.ui.singleFilesPage
        self.split_files_page = self.ui.splitFilesPage
        self.files_split_view = self.ui.filesSplitView
        self.single_files_container = self.ui.singleFilesContainer
        self.docx_files_container = self.ui.docxFilesContainer
        self.pdf_files_container = self.ui.pdfFilesContainer
        self.errors_box = self.ui.errorsCard
        self.errors_title = self.ui.errorsTitle
        self.errors_count_badge = self.ui.errorsCountBadge
        self.errors_output = self.ui.errorsOutput
        self.action_hint = self.ui.actionHint
        self.open_output_button = self.ui.openOutputButton
        self.open_log_button = self.ui.openLogButton

        self.form_root.setObjectName("resultsPageBody")
        self.summary_title.setObjectName("workflowCardTitle")
        self.files_title.setObjectName("workflowCardTitle")
        self.errors_title.setObjectName("workflowCardTitle")
        self._bind_translation(self.summary_title, "upper_text", "group.run_summary")
        self._bind_translation(self.files_title, "upper_text", "group.generated_files")
        self._bind_translation(self.errors_title, "upper_text", "group.errors")
        self._bind_translation(self.action_hint, "text", "results.action_hint")
        self._bind_translation(self.open_output_button, "text", "button.open_output_folder")
        self._bind_translation(self.open_log_button, "text", "button.open_log")

        self.single_files_panel = ResultsFilesPanel(
            list_object_name="filesList",
            badge_object_name="singleFilesCountBadge",
            title_visible=False,
        )
        self.docx_files_panel = ResultsFilesPanel(
            list_object_name="docxFilesList",
            badge_object_name="docxFilesCountBadge",
        )
        self.pdf_files_panel = ResultsFilesPanel(
            list_object_name="pdfFilesList",
            badge_object_name="pdfFilesCountBadge",
        )
        self._attach_panel(self.single_files_container, self.single_files_panel)
        self._attach_panel(self.docx_files_container, self.docx_files_panel)
        self._attach_panel(self.pdf_files_container, self.pdf_files_panel)

        self.files_list = self.single_files_panel.list_widget
        self.docx_files_title = self.docx_files_panel.title_label
        self.docx_files_count_badge = self.docx_files_panel.count_badge
        self.docx_files_list = self.docx_files_panel.list_widget
        self.pdf_files_title = self.pdf_files_panel.title_label
        self.pdf_files_count_badge = self.pdf_files_panel.count_badge
        self.pdf_files_list = self.pdf_files_panel.list_widget
        self._bind_translation(self.docx_files_title, "upper_text", "group.generated_docx")
        self._bind_translation(self.pdf_files_title, "upper_text", "group.generated_pdf")

        self.summary_label.setWordWrap(True)
        self.summary_label.setTextFormat(Qt.RichText)
        self.summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.results_status_title.setWordWrap(True)
        self.results_status_hint.setWordWrap(True)
        self.action_hint.setWordWrap(True)

        self.files_box.setMinimumHeight(PANEL_MIN_HEIGHT + 20)
        self.files_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        self.files_view_stack.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.files_split_view.setChildrenCollapsible(False)
        self.files_split_view.setHandleWidth(10)
        self.files_split_view.setStretchFactor(0, 1)
        self.files_split_view.setStretchFactor(1, 1)

        self.errors_box.setMinimumHeight(PANEL_MIN_HEIGHT + 40)
        self.errors_output.setReadOnly(True)
        self.errors_output.setMinimumHeight(PANEL_MIN_HEIGHT)
        self.open_output_button.clicked.connect(self._open_output_folder)
        self.open_log_button.clicked.connect(self._open_log)
        self.retranslate_ui()

    def bind_result(self, result: GenerationResult, session: ProjectSession):
        self.result = result
        self.session = session
        self.refresh_from_session()

    def refresh_from_session(self):
        docx_paths = list(self.result.generated_docx_paths)
        pdf_paths = list(self.result.generated_pdf_paths)
        total_files = len(docx_paths) + len(pdf_paths)
        error_count = len(self.result.errors)

        self.summary_label.setText(self._build_summary_markup(total_files, error_count))
        self._refresh_visual_state(total_files, error_count)

        split_mode = bool(docx_paths and pdf_paths)
        self.files_count_badge.setVisible(not split_mode)

        if split_mode:
            self.files_view_stack.setCurrentWidget(self.split_files_page)
            self.docx_files_panel.populate_entries(
                paths=docx_paths,
                open_label=self.localization.t("button.open"),
                on_open=self._open_path,
                empty_text=self.localization.t("results.files.empty"),
            )
            self.pdf_files_panel.populate_entries(
                paths=pdf_paths,
                open_label=self.localization.t("button.open"),
                on_open=self._open_path,
                empty_text=self.localization.t("results.files.empty"),
            )
            self.docx_files_count_badge.setText(str(len(docx_paths)))
            self.pdf_files_count_badge.setText(str(len(pdf_paths)))
            self._set_state_property(self.docx_files_count_badge, "neutral")
            self._set_state_property(self.pdf_files_count_badge, "neutral")
            self.files_split_view.setSizes([1, 1])
        else:
            self.files_view_stack.setCurrentWidget(self.single_files_page)
            self.single_files_panel.populate_entries(
                paths=[*docx_paths, *pdf_paths],
                open_label=self.localization.t("button.open"),
                on_open=self._open_path,
                empty_text=self.localization.t("results.files.empty"),
            )
            self.docx_files_list.clear()
            self.pdf_files_list.clear()
            self.docx_files_count_badge.clear()
            self.pdf_files_count_badge.clear()

        self._sync_files_stack_height(split_mode)

        if self.result.errors:
            translated = [self.localization.translate_runtime_text(error) for error in self.result.errors]
            self.errors_output.setPlainText("\n".join(translated))
        else:
            self.errors_output.clear()
        self.errors_box.setVisible(bool(self.result.errors))

    def _build_summary_markup(self, total_files: int, error_count: int) -> str:
        rows: list[tuple[str, str, bool]] = []
        if total_files or self.result.total_rows:
            rows.extend(
                [
                    (
                        self.localization.t("results.metric.docx_created"),
                        self.localization.t(
                            "results.created_docx",
                            success_count=self.result.success_count,
                            total_rows=self.result.total_rows,
                        ),
                        False,
                    ),
                    (
                        self.localization.t("results.metric.pdf_generated"),
                        str(len(self.result.generated_pdf_paths)),
                        False,
                    ),
                    (
                        self.localization.t("results.metric.files_available"),
                        str(total_files),
                        False,
                    ),
                ]
            )
            if self.result.log_path:
                rows.append(
                    (
                        self.localization.t("results.metric.log_file"),
                        self.result.log_path,
                        True,
                    )
                )
        else:
            rows.append(
                (
                    self.localization.t("group.run_summary"),
                    self.localization.t("status.no_generation_results"),
                    False,
                )
            )
            if self.result.log_path:
                rows.append(
                    (
                        self.localization.t("results.metric.log_file"),
                        self.result.log_path,
                        True,
                    )
                )
            if error_count:
                rows.append(
                    (
                        self.localization.t("group.errors"),
                        self.localization.t("results.error_count", count=error_count),
                        False,
                    )
                )

        rendered_rows = "".join(
            self._summary_row(label=label, value=value, monospace=monospace)
            for label, value, monospace in rows
        )
        return (
            "<html><body>"
            "<table width='100%' cellspacing='0' cellpadding='0'>"
            f"{rendered_rows}"
            "</table>"
            "</body></html>"
        )

    def _summary_row(self, *, label: str, value: str, monospace: bool) -> str:
        safe_label = escape(label)
        safe_value = escape(str(value))
        value_style = "font-family: 'JetBrains Mono', 'Cascadia Mono', 'Consolas', monospace;" if monospace else ""
        return (
            "<tr>"
            "<td valign='top' width='176' style='padding: 0 18px 10px 0; font-size: 12px; font-weight: 700;'>"
            f"{safe_label}"
            "</td>"
            "<td valign='top' style='padding: 0 0 10px 0; font-size: 13px;"
            f"{value_style}'>"
            f"{safe_value}"
            "</td>"
            "</tr>"
        )

    def _refresh_visual_state(self, total_files: int, error_count: int):
        if total_files == 0 and error_count == 0 and not self.result.log_path:
            badge = self.localization.t("results.badge.empty").upper()
            title = self.localization.t("results.status.empty_title")
            hint = self.localization.t("results.status.empty_detail")
            status = "empty"
        elif error_count or (self.result.total_rows and self.result.success_count < self.result.total_rows):
            badge = self.localization.t("results.badge.warning").upper()
            title = self.localization.t("results.status.warning_title")
            hint = self.localization.t("results.status.warning_detail")
            status = "warning"
        else:
            badge = self.localization.t("results.badge.success").upper()
            title = self.localization.t("results.status.success_title")
            hint = self.localization.t("results.status.success_detail")
            status = "success"

        self.results_status_badge.setText(badge)
        self.results_status_title.setText(title)
        self.results_status_hint.setText(hint)
        self.files_count_badge.setText(str(total_files))
        self.errors_count_badge.setText(
            self.localization.t("results.errors.none_badge").upper() if error_count == 0 else str(error_count)
        )
        self._set_state_property(self.results_status_badge, status)
        self._set_state_property(self.files_count_badge, "neutral" if total_files else "empty")
        self._set_state_property(self.errors_count_badge, "success" if error_count == 0 else "warning")

    def _attach_panel(self, container: QWidget, panel: QWidget):
        layout = container.layout()
        if layout is None:
            layout = QVBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        layout.setAlignment(Qt.AlignTop)
        layout.addWidget(panel)

    def _sync_files_stack_height(self, split_mode: bool):
        if split_mode:
            desired = (
                self.docx_files_panel.sizeHint().height()
                + self.pdf_files_panel.sizeHint().height()
                + self.files_split_view.handleWidth()
            )
        else:
            desired = self.single_files_panel.sizeHint().height()
        desired = max(120, desired)
        self.files_view_stack.setFixedHeight(desired)

    def _set_state_property(self, widget, state: str):
        if widget.property("status") == state:
            return
        widget.setProperty("status", state)
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    def _open_path(self, path: str):
        if path:
            open_path(path)

    def _open_output_folder(self):
        if self.session.output_dir:
            open_path(self.session.output_dir)

    def _open_log(self):
        if self.result.log_path:
            open_path(self.result.log_path)

    def retranslate_page(self):
        self.refresh_from_session()

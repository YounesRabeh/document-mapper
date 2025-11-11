from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFileDialog, QMessageBox, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
import os
import mimetypes


class DragDrop:
    def create_drag_drop_area(self, width, height, allowed_extensions=None, on_files_selected=None):
        if allowed_extensions is None:
            allowed_extensions = ['.txt', '.pdf', '.doc', '.docx', '.png', '.jpg', '.jpeg']

        widget = QWidget()
        widget.setMinimumSize(width, height)
        widget.setAcceptDrops(True)

        widget.on_files_selected = on_files_selected
        widget.allowed_extensions = [ext.lower() for ext in allowed_extensions]

        # Label for drag-drop area
        label = QLabel("📁 Click to browse files\nor drag & drop files here", widget)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        label.setObjectName("dragDropLabel")  # Easy reference later
        widget.drag_label = label

        layout = QVBoxLayout(widget)
        layout.addWidget(label)
        layout.setAlignment(Qt.AlignCenter)

        widget.setStyleSheet("""
            QWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            QWidget:hover {
                border-color: #007bff;
                background-color: #e9ecef;
            }
            QLabel {
                color: #333;
                font-size: 13px;
            }
        """)

        # Mouse press event (open file dialog)
        def mouse_press_event(event):
            if event.button() == Qt.LeftButton:
                self._open_file_dialog(widget)
            else:
                QWidget.mousePressEvent(widget, event)

        widget.mousePressEvent = mouse_press_event
        widget.dragEnterEvent = lambda event: self._drag_enter_event(widget, event)
        widget.dragMoveEvent = lambda event: self._drag_move_event(widget, event)
        widget.dropEvent = lambda event: self._drop_event(widget, event)

        return widget

    def _open_file_dialog(self, widget):
        """Open file dialog to select files"""
        files, _ = QFileDialog.getOpenFileNames(
            widget,
            "Select Files",
            "",
            f"Allowed files ({' '.join(['*' + ext for ext in widget.allowed_extensions])})"
        )
        if files:
            valid_files = self._filter_files_by_extension(files, widget.allowed_extensions)
            if valid_files:
                self._process_selected_files(widget, valid_files)
            else:
                self._show_error_dialog(widget, "No valid files selected")

    def _drag_enter_event(self, widget, event: QDragEnterEvent):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            valid_files = [
                url.toLocalFile() for url in urls
                if url.isLocalFile() and os.path.splitext(url.toLocalFile())[1].lower() in widget.allowed_extensions
            ]
            if valid_files:
                event.acceptProposedAction()
                widget.setStyleSheet("""
                    QWidget {
                        border: 2px dashed #28a745;
                        border-radius: 10px;
                        background-color: #d4edda;
                    }
                    QLabel {
                        color: #155724;
                        font-size: 13px;
                    }
                """)
            else:
                event.ignore()
                widget.setStyleSheet("""
                    QWidget {
                        border: 2px dashed #dc3545;
                        border-radius: 10px;
                        background-color: #f8d7da;
                    }
                    QLabel {
                        color: #721c24;
                        font-size: 13px;
                    }
                """)
        else:
            event.ignore()

    def _drag_move_event(self, widget, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def _drop_event(self, widget, event: QDropEvent):
        """Handle file drop"""
        # Reset style
        widget.setStyleSheet("""
            QWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f8f9fa;
            }
            QWidget:hover {
                border-color: #007bff;
                background-color: #e9ecef;
            }
            QLabel {
                color: #333;
                font-size: 13px;
            }
        """)

        if event.mimeData().hasUrls():
            files = [
                url.toLocalFile() for url in event.mimeData().urls()
                if url.isLocalFile() and os.path.isfile(url.toLocalFile())
            ]
            if files:
                valid_files = self._filter_files_by_extension(files, widget.allowed_extensions)
                if valid_files:
                    self._process_selected_files(widget, valid_files)
                else:
                    self._show_error_dialog(widget, "No files with allowed extensions were dropped")

            event.acceptProposedAction()

    def _filter_files_by_extension(self, files, allowed_extensions):
        """Filter only files with allowed extensions"""
        return [f for f in files if os.path.splitext(f)[1].lower() in allowed_extensions]

    def _process_selected_files(self, widget, files):
        """Process selected or dropped files"""
        label = widget.drag_label
        if len(files) == 1:
            file_name = os.path.basename(files[0])
            mime_type, _ = mimetypes.guess_type(files[0])
            label.setText(f"✅ <b>{file_name}</b><br><i>{mime_type or 'Unknown type'}</i>")
        else:
            label.setText(f"✅ {len(files)} files selected")

        if widget.on_files_selected:
            widget.on_files_selected(files)
        else:
            print(f"Selected files: {files}")

    def _show_error_dialog(self, widget, message):
        QMessageBox.warning(widget, "Invalid Files", message)

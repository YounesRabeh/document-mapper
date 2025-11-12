from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox, QHBoxLayout
from gui.stages.base_stage import BaseStage, UIFactory
from gui.ui.custom_menu_bar import CustomMenuBar


class Stage1(BaseStage):
    def __init__(self, config: dict):
        super().__init__(config, "🟢 Stage 1: Start")
        self.add_menu(CustomMenuBar.default(self))

        # --- Split Layout (horizontal) ---
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)
        split_layout.setContentsMargins(20, 20, 20, 20)

        # Left: Excel files (.xlsx)
        xlsx_area = UIFactory.create_drag_drop_area(
            width=300, height=300,
            allowed_extensions=['.xlsx'],
            on_files_selected=lambda files: print("Excel files:", files)
        )

        # Right: Word files (.docx)
        docx_area = UIFactory.create_drag_drop_area(
            width=300, height=300,
            allowed_extensions=['.docx'],
            on_files_selected=lambda files: print("Word files:", files)
        )

        # Add to split layout with stretch factors
        split_layout.addWidget(xlsx_area, alignment=Qt.AlignCenter)
        split_layout.addWidget(docx_area, alignment=Qt.AlignCenter)

        # Add the split layout to the main layout
        self.main_layout.addLayout(split_layout, stretch=1)

        # --- Bottom Button ---
        next_btn = UIFactory.create_button("Next → Stage 2", self.next_stage.emit)
        next_btn.setFixedWidth(160)
        self.main_layout.addWidget(next_btn, alignment=Qt.AlignCenter)

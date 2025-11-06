from PySide6.QtWidgets import QMainWindow, QStackedWidget
from PySide6.QtCore import Qt

from core.enums.log_level import LogLevel
from core.manager.theme_manager import ThemeManager
from core.util.logger import Logger
from gui.stages.stage1 import Stage1
from gui.stages.stage2 import Stage2
from gui.stages.stage3 import Stage3


class MainWindow(QMainWindow):
    """Main window that manages multiple stages (1–3)."""
    initial_stage_index: int = 1

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        ThemeManager(config)
        # Window setup
        self.setWindowTitle(self.config.get("WINDOW_TITLE", "Document Mapper"))
        self.resize(self.config.get("WINDOW_WIDTH", 800), self.config.get("WINDOW_HEIGHT", 500))
        self.setMinimumSize(
            self.config.get("WINDOW_MIN_WIDTH", 400),
            self.config.get("WINDOW_MIN_HEIGHT", 300)
        )

        # Stage manager (stacked widget)
        self.stage_manager = QStackedWidget()
        self.setCentralWidget(self.stage_manager)

        # Instantiate all stages
        self.stage1 = Stage1(self.config)
        self.stage2 = Stage2(self.config)
        self.stage3 = Stage3(self.config)

        # Add to manager
        self.stage_manager.addWidget(self.stage1)
        self.stage_manager.addWidget(self.stage2)
        self.stage_manager.addWidget(self.stage3)

        # Connect navigation
        self.stage1.next_stage.connect(lambda: self.goto_stage(2))
        self.stage2.prev_stage.connect(lambda: self.goto_stage(1))
        self.stage2.next_stage.connect(lambda: self.goto_stage(3))
        self.stage3.prev_stage.connect(lambda: self.goto_stage(2))

        # Start at Stage 1
        self.goto_stage(self.initial_stage_index)

    def goto_stage(self, index: int):
        """Switch to a specific stage (1-based index)."""
        self.stage_manager.setCurrentIndex(index - 1)
        Logger.log(f"Switched to Stage {index}", LogLevel.DEBUG)

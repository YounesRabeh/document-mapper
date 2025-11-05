from core.manager.theme_manager import ThemeManager
from gui.stages.base_stage import BaseStage, UIFactory


class Stage1(BaseStage):
    def __init__(self, config: dict):
        super().__init__(config, "🟢 Stage 1: Start")

        # Add “Next” button (right-aligned)
        next_btn = UIFactory.create_button("Next → Stage 2", self.next_stage.emit)
        theme_btn = UIFactory.create_button("Theme", ThemeManager.toggle_theme)
        self.main_layout.addWidget(next_btn)
        self.main_layout.addWidget(theme_btn)

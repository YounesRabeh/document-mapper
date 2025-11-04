from gui.stages.base_stage import BaseStage, UIFactory


class Stage3(BaseStage):
    def __init__(self, config: dict):
        super().__init__(config, "🔵 Stage 3: Done")

        back_btn = UIFactory.create_button("← Back to Stage 2", self.prev_stage.emit)
        self.main_layout.addWidget(back_btn)

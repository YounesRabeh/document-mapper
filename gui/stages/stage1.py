from gui.stages.base_stage import BaseStage, UIFactory


class Stage1(BaseStage):
    def __init__(self, config: dict):
        super().__init__(config, "🟢 Stage 1: Start")

        # Add “Next” button (right-aligned)
        next_btn = UIFactory.create_button("Next → Stage 2", self.next_stage.emit)
        self.main_layout.addWidget(next_btn)

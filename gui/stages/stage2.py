from core.util.resources import Resources
from gui.stages.base_stage import BaseStage, UIFactory


class Stage2(BaseStage):
    def __init__(self, config: dict):
        super().__init__(config, "🟡 Stage 2: Processing")

        entry = UIFactory.create_file_entry(
            Resources.get_in_templates("docx_template_test.docx"),

        )
        entry2 = UIFactory.create_file_entry(
            Resources.get_in_data("xlsx_test.xlsx")
        )


        # Add Back + Next buttons
        nav_layout = UIFactory.create_button("← Back to Stage 1", self.prev_stage.emit)
        next_btn = UIFactory.create_button("Next → Stage 3", self.next_stage.emit)

        # Arrange horizontally

        self.main_layout.addWidget(entry)
        self.main_layout.addWidget(entry2)
        self.main_layout.addWidget(nav_layout)
        self.main_layout.addWidget(next_btn)


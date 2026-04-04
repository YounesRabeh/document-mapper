from __future__ import annotations

from core.certificate.models import GenerationResult, ProjectSession
from gui.controllers import WorkflowStateController


class _GeneratorStub:
    def __init__(self, errors: list[str] | None = None):
        self._errors = list(errors or [])

    def validate_session(self, _session: ProjectSession) -> list[str]:
        return list(self._errors)


def test_compute_states_blocks_generate_and_results_until_ready():
    controller = WorkflowStateController(_GeneratorStub(errors=["missing data"]))

    states = controller.compute_states(ProjectSession(), GenerationResult(), current_stage=2, stage_count=4)

    assert states[1].completed is True
    assert states[2].blocked is True
    assert states[2].active is False
    assert states[3].blocked is True
    assert states[4].blocked is True


def test_compute_states_unlocks_generate_and_results_when_inputs_and_results_exist():
    controller = WorkflowStateController(_GeneratorStub(errors=[]))
    result = GenerationResult(total_rows=3, success_count=3, generated_docx_paths=["/tmp/out.docx"])

    states = controller.compute_states(ProjectSession(), result, current_stage=4, stage_count=4)

    assert states[3].completed is True
    assert states[4].active is True
    assert states[4].blocked is False


def test_resolve_fallback_stage_returns_highest_available_stage():
    controller = WorkflowStateController(_GeneratorStub(errors=["still blocked"]))

    fallback = controller.resolve_fallback_stage(
        last_valid_stage=4,
        session=ProjectSession(),
        last_result=GenerationResult(),
        current_stage=4,
        stage_count=4,
    )

    assert fallback == 1

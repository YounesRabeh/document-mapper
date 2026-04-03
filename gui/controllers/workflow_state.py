from __future__ import annotations

from dataclasses import dataclass

from core.certificate.models import GenerationResult, ProjectSession


@dataclass(slots=True)
class WorkflowStageState:
    active: bool = False
    completed: bool = False
    blocked: bool = False


class WorkflowStateController:
    def __init__(self, generator):
        self.generator = generator

    def compute_states(
        self,
        session: ProjectSession,
        last_result: GenerationResult,
        current_stage: int,
        stage_count: int,
    ) -> dict[int, WorkflowStageState]:
        current_stage = max(1, min(current_stage, stage_count or 1))
        generate_available = not self.generator.validate_session(session)
        results_available = self.has_generation_results(last_result)
        blocked_by_stage = {
            1: False,
            2: False,
            3: not generate_available,
            4: not results_available,
        }
        return {
            index: WorkflowStageState(
                active=index == current_stage and not blocked_by_stage[index],
                completed=index < current_stage and not blocked_by_stage[index],
                blocked=blocked_by_stage[index],
            )
            for index in range(1, stage_count + 1)
        }

    def can_navigate_to_stage(
        self,
        stage: int,
        session: ProjectSession,
        last_result: GenerationResult,
        current_stage: int,
        stage_count: int,
    ) -> bool:
        if stage < 1 or stage > stage_count:
            return False
        return not self.compute_states(session, last_result, current_stage, stage_count)[stage].blocked

    def resolve_fallback_stage(
        self,
        last_valid_stage: int,
        session: ProjectSession,
        last_result: GenerationResult,
        current_stage: int,
        stage_count: int,
    ) -> int:
        if self.can_navigate_to_stage(last_valid_stage, session, last_result, current_stage, stage_count):
            return last_valid_stage
        for stage in range(stage_count, 0, -1):
            if self.can_navigate_to_stage(stage, session, last_result, current_stage, stage_count):
                return stage
        return 1

    @staticmethod
    def has_generation_results(result: GenerationResult) -> bool:
        return any(
            (
                result.total_rows,
                result.generated_docx_paths,
                result.generated_pdf_paths,
                result.log_path,
                result.errors,
            )
        )

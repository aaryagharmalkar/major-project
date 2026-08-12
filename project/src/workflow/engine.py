"""Generic ordered workflow engine; it deliberately contains no case business logic."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from .context import WorkflowContext, WorkflowRunResult
from .exceptions import InvalidStageResultError
from .registry import StageRegistry
from .state import StageStatus, WorkflowExecutionReport, utc_now


class WorkflowEngine:
    """Executes registered stages, retaining state for resume and review."""

    def __init__(
        self,
        registry: StageRegistry,
        *,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self._registry = registry
        self._clock = clock

    def run(self, context: WorkflowContext) -> WorkflowRunResult:
        started_at = self._clock()
        stages = self._registry.stages
        state = context.execution_state.register_stages(stage.name for stage in stages)
        current_context = context.with_updates(execution_state=state)
        stopped_on_critical_failure = False

        for stage in stages:
            record = current_context.execution_state.record_for(stage.name)
            if record is not None and record.status == StageStatus.COMPLETED:
                continue

            if not stage.can_run(current_context):
                state = current_context.execution_state.mark_skipped(stage.name, self._clock())
                current_context = current_context.with_updates(execution_state=state)
                continue

            state = current_context.execution_state.mark_running(stage.name, self._clock())
            current_context = current_context.with_updates(execution_state=state)
            try:
                stage_context = stage.execute(current_context)
                if not isinstance(stage_context, WorkflowContext):
                    raise InvalidStageResultError(
                        f"Stage '{stage.name}' must return WorkflowContext"
                    )
                if stage_context.case_id != current_context.case_id:
                    raise InvalidStageResultError(
                        f"Stage '{stage.name}' returned a context for another case"
                    )
                state = current_context.execution_state.mark_completed(stage.name, self._clock())
                current_context = stage_context.with_updates(execution_state=state)
            except Exception as exc:  # Stage failures become inspectable state, not lost context.
                state = current_context.execution_state.mark_failed(stage.name, self._clock(), exc)
                current_context = current_context.with_updates(execution_state=state)
                if stage.is_critical:
                    stopped_on_critical_failure = True
                    break

        finished_at = self._clock()
        report = WorkflowExecutionReport(
            case_id=current_context.case_id,
            started_at=started_at,
            finished_at=finished_at,
            stage_records=current_context.execution_state.stage_records,
            stopped_on_critical_failure=stopped_on_critical_failure,
        )
        return WorkflowRunResult(context=current_context, report=report)

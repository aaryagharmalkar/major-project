from datetime import datetime, timedelta, timezone
import unittest
from uuid import uuid4

from src.workflow.context import ContextItem, WorkflowContext
from src.workflow.engine import WorkflowEngine
from src.workflow.registry import StageRegistry
from src.workflow.stage import WorkflowStage
from src.workflow.state import StageStatus, WorkflowState


class RecordingStage(WorkflowStage):
    def __init__(self, name: str, calls: list[str], *, can_run: bool = True, fail: bool = False, critical: bool = True) -> None:
        self.name = name
        self.calls = calls
        self._can_run = can_run
        self._fail = fail
        self.is_critical = critical
        self.observed_statuses: list[StageStatus] = []

    def can_run(self, context: WorkflowContext) -> bool:
        return self._can_run

    def execute(self, context: WorkflowContext) -> WorkflowContext:
        self.calls.append(self.name)
        record = context.execution_state.record_for(self.name)
        assert record is not None
        self.observed_statuses.append(record.status)
        if self._fail:
            raise RuntimeError(f"{self.name} failed")
        return context.with_updates(metadata=context.metadata + (ContextItem(key=self.name, value="done"),))


class IncrementingClock:
    def __init__(self) -> None:
        self.value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(milliseconds=10)
        return current


class WorkflowEngineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_id = uuid4()
        self.context = WorkflowContext(
            case_id=self.case_id,
            execution_state=WorkflowState(case_id=self.case_id),
        )
        self.clock = IncrementingClock()

    def test_executes_registered_stages_in_order_and_propagates_context(self) -> None:
        calls: list[str] = []
        first = RecordingStage("first", calls)
        second = RecordingStage("second", calls)
        result = WorkflowEngine(StageRegistry([first, second]), clock=self.clock).run(self.context)

        self.assertEqual(calls, ["first", "second"])
        self.assertEqual([item.key for item in result.context.metadata], ["first", "second"])
        self.assertEqual(first.observed_statuses, [StageStatus.RUNNING])
        self.assertTrue(result.report.successful)
        self.assertGreater(result.report.duration_ms, 0)

    def test_stage_can_register_itself_with_registry(self) -> None:
        calls: list[str] = []
        registry = StageRegistry()
        stage = RecordingStage("self-registered", calls)

        registered = stage.register_with(registry)

        self.assertIs(registered, stage)
        self.assertEqual(registry.stages, (stage,))

    def test_skips_completed_and_non_runnable_stages(self) -> None:
        calls: list[str] = []
        completed = RecordingStage("completed", calls)
        skipped = RecordingStage("skipped", calls, can_run=False)
        state = WorkflowState(case_id=self.case_id).register_stages(["completed"])
        state = state.mark_running("completed", self.clock())
        state = state.mark_completed("completed", self.clock())
        context = self.context.with_updates(execution_state=state)

        result = WorkflowEngine(StageRegistry([completed, skipped]), clock=self.clock).run(context)

        self.assertEqual(calls, [])
        self.assertEqual(result.context.execution_state.record_for("completed").status, StageStatus.COMPLETED)
        self.assertEqual(result.context.execution_state.record_for("skipped").status, StageStatus.SKIPPED)

    def test_critical_failure_preserves_context_and_stops_later_stages(self) -> None:
        calls: list[str] = []
        failing = RecordingStage("failing", calls, fail=True)
        later = RecordingStage("later", calls)
        result = WorkflowEngine(StageRegistry([failing, later]), clock=self.clock).run(self.context)

        record = result.context.execution_state.record_for("failing")
        self.assertEqual(calls, ["failing"])
        self.assertEqual(record.status, StageStatus.FAILED)
        self.assertEqual(record.exception.exception_type, "RuntimeError")
        self.assertTrue(result.report.stopped_on_critical_failure)
        self.assertFalse(result.report.successful)
        self.assertEqual(result.context.execution_state.record_for("later").status, StageStatus.PENDING)

    def test_noncritical_failure_allows_later_stages(self) -> None:
        calls: list[str] = []
        failing = RecordingStage("failing", calls, fail=True, critical=False)
        later = RecordingStage("later", calls)
        result = WorkflowEngine(StageRegistry([failing, later]), clock=self.clock).run(self.context)

        self.assertEqual(calls, ["failing", "later"])
        self.assertEqual(result.context.execution_state.record_for("later").status, StageStatus.COMPLETED)
        self.assertFalse(result.report.stopped_on_critical_failure)


if __name__ == "__main__":
    unittest.main()

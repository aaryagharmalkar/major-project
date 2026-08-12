"""Immutable execution state and reports for resumable workflow runs."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Iterable
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExceptionInfo(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    exception_type: str
    message: str


class StageExecutionRecord(BaseModel):
    """Latest lifecycle record for one named workflow stage."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    stage_name: str
    status: StageStatus = StageStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    exception: ExceptionInfo | None = None


class WorkflowState(BaseModel):
    """Controlled state snapshot carried within every WorkflowContext."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: UUID
    stage_records: tuple[StageExecutionRecord, ...] = ()
    updated_at: datetime = Field(default_factory=utc_now)

    def record_for(self, stage_name: str) -> StageExecutionRecord | None:
        return next((record for record in self.stage_records if record.stage_name == stage_name), None)

    def register_stages(self, stage_names: Iterable[str]) -> "WorkflowState":
        records = list(self.stage_records)
        known_names = {record.stage_name for record in records}
        records.extend(
            StageExecutionRecord(stage_name=name)
            for name in stage_names
            if name not in known_names
        )
        return self._with_records(records)

    def mark_running(self, stage_name: str, started_at: datetime) -> "WorkflowState":
        return self._replace_record(
            StageExecutionRecord(
                stage_name=stage_name,
                status=StageStatus.RUNNING,
                started_at=started_at,
            )
        )

    def mark_completed(self, stage_name: str, finished_at: datetime) -> "WorkflowState":
        return self._finish(stage_name, StageStatus.COMPLETED, finished_at)

    def mark_skipped(self, stage_name: str, finished_at: datetime) -> "WorkflowState":
        return self._finish(stage_name, StageStatus.SKIPPED, finished_at)

    def mark_failed(
        self,
        stage_name: str,
        finished_at: datetime,
        exception: Exception,
    ) -> "WorkflowState":
        current = self._require_record(stage_name)
        started_at = current.started_at or finished_at
        return self._replace_record(
            StageExecutionRecord(
                stage_name=stage_name,
                status=StageStatus.FAILED,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=max((finished_at - started_at).total_seconds() * 1000, 0),
                exception=ExceptionInfo(
                    exception_type=type(exception).__name__,
                    message=str(exception),
                ),
            )
        )

    def _finish(
        self,
        stage_name: str,
        status: StageStatus,
        finished_at: datetime,
    ) -> "WorkflowState":
        current = self._require_record(stage_name)
        started_at = current.started_at or finished_at
        return self._replace_record(
            StageExecutionRecord(
                stage_name=stage_name,
                status=status,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=max((finished_at - started_at).total_seconds() * 1000, 0),
            )
        )

    def _replace_record(self, replacement: StageExecutionRecord) -> "WorkflowState":
        records = tuple(
            replacement if record.stage_name == replacement.stage_name else record
            for record in self.stage_records
        )
        if not any(record.stage_name == replacement.stage_name for record in self.stage_records):
            records += (replacement,)
        return self._with_records(records)

    def _require_record(self, stage_name: str) -> StageExecutionRecord:
        record = self.record_for(stage_name)
        if record is None:
            raise ValueError(f"Stage '{stage_name}' is not registered in workflow state")
        return record

    def _with_records(self, records: Iterable[StageExecutionRecord]) -> "WorkflowState":
        return self.model_copy(update={"stage_records": tuple(records), "updated_at": utc_now()})


class WorkflowExecutionReport(BaseModel):
    """Read-only report returned even when a stage fails."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    case_id: UUID
    started_at: datetime
    finished_at: datetime
    stage_records: tuple[StageExecutionRecord, ...]
    stopped_on_critical_failure: bool = False

    @property
    def duration_ms(self) -> float:
        return max((self.finished_at - self.started_at).total_seconds() * 1000, 0)

    @property
    def successful(self) -> bool:
        return not any(record.status == StageStatus.FAILED for record in self.stage_records)

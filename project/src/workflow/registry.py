"""Ordered registry that keeps the engine independent of concrete stage classes."""

from __future__ import annotations

from typing import Iterable

from .exceptions import DuplicateStageError, StageRegistrationError
from .stage import WorkflowStage


class StageRegistry:
    """Owns stage registration order; applications compose stages through it."""

    def __init__(self, stages: Iterable[WorkflowStage] = ()) -> None:
        self._stages: list[WorkflowStage] = []
        for stage in stages:
            self.register(stage)

    def register(self, stage: WorkflowStage) -> WorkflowStage:
        if not isinstance(stage, WorkflowStage):
            raise StageRegistrationError("Registered objects must implement WorkflowStage")
        if not getattr(stage, "name", "").strip():
            raise StageRegistrationError("Every workflow stage must define a non-empty name")
        if any(existing.name == stage.name for existing in self._stages):
            raise DuplicateStageError(f"Stage '{stage.name}' is already registered")
        self._stages.append(stage)
        return stage

    @property
    def stages(self) -> tuple[WorkflowStage, ...]:
        return tuple(self._stages)

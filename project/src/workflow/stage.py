"""Common stage contract used by all future processing modules."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from .context import WorkflowContext

if TYPE_CHECKING:
    from .registry import StageRegistry


class WorkflowStage(ABC):
    """A modular, idempotent unit of orchestration with no engine coupling."""

    name: str
    is_critical: bool = True

    @abstractmethod
    def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Return the next immutable workflow context snapshot."""

    def can_run(self, context: WorkflowContext) -> bool:
        """Allow a stage to opt out when its prerequisites are absent."""
        return True

    def register_with(self, registry: "StageRegistry") -> "WorkflowStage":
        """Register this stage without coupling the engine to its concrete type."""
        return registry.register(self)

    def rollback(self, context: WorkflowContext) -> WorkflowContext:
        """Placeholder hook for a future compensating-action implementation."""
        return context

"""Exceptions raised only by the reusable workflow orchestration layer."""


class WorkflowError(RuntimeError):
    """Base exception for workflow-engine failures."""


class DuplicateStageError(WorkflowError):
    """Raised when a registry receives the same stage name more than once."""


class StageRegistrationError(WorkflowError):
    """Raised when an invalid stage is registered."""


class StageExecutionError(WorkflowError):
    """Wraps an exception raised by an individual workflow stage."""

    def __init__(self, stage_name: str, cause: Exception) -> None:
        super().__init__(f"Stage '{stage_name}' failed: {cause}")
        self.stage_name = stage_name
        self.cause = cause


class InvalidStageResultError(WorkflowError):
    """Raised when a stage returns a value other than WorkflowContext."""

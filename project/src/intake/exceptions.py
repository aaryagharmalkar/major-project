"""Document-intake errors kept separate from workflow-engine errors."""


class DocumentIntakeError(RuntimeError):
    """Base exception for local upload intake failures."""


class UploadSourceNotFoundError(DocumentIntakeError):
    """Raised when a requested local upload no longer exists."""


class StorageLayoutError(DocumentIntakeError):
    """Raised when the deterministic case storage layout cannot be created."""

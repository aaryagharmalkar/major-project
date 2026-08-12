"""Deterministic per-case paths for original and future derived upload artifacts."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

from .exceptions import StorageLayoutError


@dataclass(frozen=True)
class CaseStorageLayout:
    root: Path
    case_id: UUID

    @property
    def case_directory(self) -> Path:
        return self.root / f"CASE_{self.case_id.hex}"

    @property
    def originals_directory(self) -> Path:
        return self.case_directory / "originals"

    @property
    def processed_directory(self) -> Path:
        return self.case_directory / "processed"

    @property
    def thumbnails_directory(self) -> Path:
        return self.case_directory / "thumbnails"

    def ensure_exists(self) -> "CaseStorageLayout":
        try:
            root = self.root.resolve()
            case_directory = self.case_directory.resolve()
            if case_directory.parent != root:
                raise StorageLayoutError("Case storage path escapes configured storage root")
            for directory in (self.originals_directory, self.processed_directory, self.thumbnails_directory):
                directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StorageLayoutError(f"Could not create case upload layout: {exc}") from exc
        return self

    def original_path(self, document_id: UUID, extension: str) -> Path:
        return self.originals_directory / f"{document_id}{extension.lower()}"

    def copy_original(self, source: Path, document_id: UUID, extension: str) -> Path:
        target = self.original_path(document_id, extension)
        try:
            root = self.root.resolve()
            resolved_target = target.resolve()
            if not resolved_target.is_relative_to(root) or not resolved_target.is_relative_to(self.case_directory.resolve()):
                raise StorageLayoutError("Stored upload path escapes its case directory")
            shutil.copy2(source, target)
        except OSError as exc:
            raise StorageLayoutError(f"Could not store original upload '{source.name}': {exc}") from exc
        return target

    def relative_key(self, path: Path) -> str:
        return path.relative_to(self.root).as_posix()

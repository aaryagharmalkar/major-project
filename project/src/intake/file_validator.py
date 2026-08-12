"""Deterministic safety checks for uploaded investigation documents."""

from __future__ import annotations

import mimetypes
import zipfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


SUPPORTED_MEDIA_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".wav": "audio/wav",
}


class FileValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    is_valid: bool
    extension: str
    detected_mime_type: str | None = None
    size_bytes: int = Field(ge=0)
    errors: tuple[str, ...] = ()


class FileValidator:
    """Validates type, size, emptiness, and a minimal format signature locally."""

    def __init__(self, max_size_bytes: int = 100 * 1024 * 1024) -> None:
        if max_size_bytes <= 0:
            raise ValueError("max_size_bytes must be positive")
        self.max_size_bytes = max_size_bytes

    def validate(self, file_path: Path) -> FileValidationResult:
        extension = file_path.suffix.lower()
        errors: list[str] = []
        if not file_path.is_file():
            return FileValidationResult(
                is_valid=False,
                extension=extension,
                size_bytes=0,
                errors=("Upload source does not exist or is not a file.",),
            )

        size_bytes = file_path.stat().st_size
        detected_mime_type = SUPPORTED_MEDIA_TYPES.get(extension) or mimetypes.guess_type(file_path.name)[0]
        if extension not in SUPPORTED_MEDIA_TYPES:
            errors.append(f"Unsupported file extension: {extension or '[none]'}.")
        if size_bytes == 0:
            errors.append("Uploaded file is empty.")
        if size_bytes > self.max_size_bytes:
            errors.append(f"Uploaded file exceeds the {self.max_size_bytes}-byte size limit.")
        if not errors and not self._has_valid_signature(file_path, extension):
            errors.append("Uploaded file failed basic corruption/signature validation.")

        return FileValidationResult(
            is_valid=not errors,
            extension=extension,
            detected_mime_type=detected_mime_type,
            size_bytes=size_bytes,
            errors=tuple(errors),
        )

    @staticmethod
    def _has_valid_signature(file_path: Path, extension: str) -> bool:
        try:
            with file_path.open("rb") as source:
                header = source.read(16)
            if extension == ".pdf":
                return header.startswith(b"%PDF-")
            if extension in {".jpg", ".jpeg"}:
                return header.startswith(b"\xff\xd8\xff")
            if extension == ".png":
                return header.startswith(b"\x89PNG\r\n\x1a\n")
            if extension == ".docx":
                with zipfile.ZipFile(file_path) as archive:
                    names = set(archive.namelist())
                return "[Content_Types].xml" in names and any(name.startswith("word/") for name in names)
            if extension in {".mp4", ".mov"}:
                return len(header) >= 12 and header[4:8] == b"ftyp"
            if extension == ".wav":
                return header.startswith(b"RIFF") and header[8:12] == b"WAVE"
        except (OSError, zipfile.BadZipFile):
            return False
        return False

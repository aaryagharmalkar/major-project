"""Streaming checksum helpers for duplicate detection and auditability."""

from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """Return the SHA-256 digest without loading the uploaded file into memory."""

    digest = hashlib.sha256()
    with file_path.open("rb") as source:
        for chunk in iter(lambda: source.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()

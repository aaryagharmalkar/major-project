"""Reference-data loading utilities for synthetic case generation.

This module is intentionally limited to reading and validating JSON reference
data from the dataset tree. It does not generate values or perform any case
construction logic.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


logger = logging.getLogger(__name__)


class ReferenceDataError(Exception):
    """Base exception for reference-data loading failures."""


class ReferenceDataNotFoundError(ReferenceDataError, FileNotFoundError):
    """Raised when an expected reference file or directory does not exist."""


class ReferenceDataFormatError(ReferenceDataError, ValueError):
    """Raised when reference data cannot be parsed as valid JSON."""


class ReferenceDataLoader:
    """Load and cache reference JSON data from a dataset root directory."""

    def __init__(self, dataset_root: str | Path) -> None:
        """Initialize the loader with the dataset root path.

        Args:
            dataset_root: Root path of the AI-ChargeSheet-Dataset repository or
                the dataset directory containing the reference data tree.
        """

        self._dataset_root = Path(dataset_root).expanduser().resolve()
        self._cache: dict[Path, Any] = {}
        self._reference_root = self._resolve_reference_root(self._dataset_root)

    @staticmethod
    def _resolve_reference_root(dataset_root: Path) -> Path:
        """Resolve the reference-data root from the provided dataset root."""

        candidates = (
            dataset_root / "dataset" / "reference_data",
            dataset_root / "reference_data",
        )
        for candidate in candidates:
            if candidate.exists() and candidate.is_dir():
                return candidate
        raise ReferenceDataNotFoundError(
            f"Could not locate a reference_data directory under '{dataset_root}'."
        )

    def _resolve_path(self, relative_path: str | Path) -> Path:
        """Resolve a relative path within the dataset tree."""

        path = Path(relative_path)
        if path.is_absolute():
            return path
        return self._dataset_root / path

    def _resolve_reference_file(self, *parts: str) -> Path:
        """Resolve a file within the reference-data tree."""

        return self._reference_root.joinpath(*parts)

    def load_json(self, path: str | Path) -> Any:
        """Load a JSON file and cache the parsed result.

        Args:
            path: Absolute path or dataset-relative path to a JSON file.

        Returns:
            The parsed JSON content.

        Raises:
            ReferenceDataNotFoundError: If the file does not exist.
            ReferenceDataFormatError: If the file is empty or invalid JSON.
        """

        resolved_path = self._resolve_path(path).resolve()

        if resolved_path in self._cache:
            logger.debug("Loaded reference JSON from cache: %s", resolved_path)
            return self._cache[resolved_path]

        if not resolved_path.exists():
            raise ReferenceDataNotFoundError(f"Reference file not found: '{resolved_path}'.")

        if not resolved_path.is_file():
            raise ReferenceDataFormatError(f"Reference path is not a file: '{resolved_path}'.")

        try:
            raw_text = resolved_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ReferenceDataError(f"Failed to read reference file '{resolved_path}': {exc}") from exc

        if not raw_text.strip():
            raise ReferenceDataFormatError(f"Reference file is empty: '{resolved_path}'.")

        try:
            payload = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ReferenceDataFormatError(
                f"Invalid JSON in reference file '{resolved_path}': {exc.msg}"
            ) from exc

        self._cache[resolved_path] = payload
        logger.debug("Loaded reference JSON from disk: %s", resolved_path)
        return payload

    def load_directory(self, directory: str | Path) -> dict[str, Any]:
        """Load all JSON files from a directory into a stem-keyed mapping.

        Args:
            directory: Absolute path or dataset-relative directory path.

        Returns:
            A mapping of file stem to parsed JSON content.

        Raises:
            ReferenceDataNotFoundError: If the directory does not exist or contains no JSON files.
            ReferenceDataFormatError: If a JSON file is malformed.
        """

        resolved_directory = self._resolve_path(directory).resolve()

        if not resolved_directory.exists():
            raise ReferenceDataNotFoundError(
                f"Reference directory not found: '{resolved_directory}'."
            )

        if not resolved_directory.is_dir():
            raise ReferenceDataFormatError(
                f"Reference path is not a directory: '{resolved_directory}'."
            )

        json_files = sorted(resolved_directory.glob("*.json"))
        if not json_files:
            raise ReferenceDataNotFoundError(
                f"No JSON files found in reference directory: '{resolved_directory}'."
            )

        loaded_data: dict[str, Any] = {}
        for json_file in json_files:
            loaded_data[json_file.stem] = self.load_json(json_file)

        return loaded_data

    def get_first_names(self) -> Any:
        """Return first-name reference data."""

        return self.load_json(self._resolve_reference_file("names", "first_names.json"))

    def get_last_names(self) -> Any:
        """Return last-name reference data."""

        return self.load_json(self._resolve_reference_file("names", "last_names.json"))

    def get_cities(self) -> Any:
        """Return city reference data."""

        return self.load_json(self._resolve_reference_file("locations", "cities.json"))

    def get_districts(self) -> Any:
        """Return district reference data."""

        return self.load_json(self._resolve_reference_file("locations", "districts.json"))

    def get_police_stations(self) -> Any:
        """Return police-station reference data."""

        return self.load_json(self._resolve_reference_file("police", "police_stations.json"))

    def get_hospitals(self) -> Any:
        """Return hospital reference data."""

        return self.load_json(self._resolve_reference_file("medical", "hospitals.json"))

    def get_weapons(self) -> Any:
        """Return weapon reference data."""

        return self.load_json(self._resolve_reference_file("medical", "weapons.json"))

    def get_bns_sections(self) -> Any:
        """Return BNS section reference data."""

        return self.load_json(self._resolve_reference_file("legal", "bns_sections.json"))

    def get_evidence_types(self) -> Any:
        """Return evidence-type reference data."""

        return self.load_json(self._resolve_reference_file("legal", "evidence_types.json"))

    def get_document_types(self) -> Any:
        """Return document-type reference data."""

        return self.load_json(self._resolve_reference_file("legal", "document_types.json"))

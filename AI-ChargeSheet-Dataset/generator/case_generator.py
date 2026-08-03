"""Master case orchestration for synthetic criminal investigation generation.

This module coordinates reference data loading, prompt rendering, Gemini
invocation, Pydantic validation, and persistence of the canonical
master_case.json artifact.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Mapping

from pydantic import ValidationError

from generator.llm.gemini import GeminiClient, GeminiRequestError, GeminiTemplateError
from generator.schemas.master_case_schema import MasterCase
from generator.utils.reference_loader import ReferenceDataLoader


logger = logging.getLogger(__name__)


class MasterCaseGenerationError(Exception):
    """Base exception for master-case generation failures."""


class MasterCasePromptError(MasterCaseGenerationError):
    """Raised when the master prompt cannot be rendered correctly."""


class MasterCaseValidationError(MasterCaseGenerationError):
    """Raised when the generated JSON does not validate as a MasterCase."""


class MasterCaseSaveError(MasterCaseGenerationError):
    """Raised when a validated MasterCase cannot be written to disk."""


class MasterCaseGenerator:
    """Generate one canonical `MasterCase` JSON file from a prompt and LLM."""

    _PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")

    def __init__(
        self,
        reference_loader: ReferenceDataLoader,
        gemini_client: GeminiClient,
        master_prompt_path: str | Path,
        output_directory: str | Path,
        *,
        validation_retries: int = 3,
    ) -> None:
        """Initialize the generator with its required collaborators.

        Args:
            reference_loader: Loader used to access reference JSON data.
            gemini_client: Client used to render prompts and call Gemini.
            master_prompt_path: Path to generator/prompts/master_case.md.
            output_directory: Directory where master_case.json will be written.
            validation_retries: Number of times to retry when schema validation fails.
        """

        if validation_retries < 1:
            raise MasterCaseGenerationError("validation_retries must be at least 1.")

        self._reference_loader = reference_loader
        self._gemini_client = gemini_client
        self._master_prompt_path = Path(master_prompt_path).expanduser().resolve()
        self._output_directory = Path(output_directory).expanduser().resolve()
        self._output_directory.mkdir(parents=True, exist_ok=True)
        self._validation_retries = validation_retries
        self._schema_json = json.dumps(MasterCase.model_json_schema(), indent=2, ensure_ascii=False)
        self._reference_data_cache: dict[str, Any] | None = None
        self._seen_case_ids = self._discover_existing_case_ids()

        if not self._master_prompt_path.exists():
            raise MasterCasePromptError(f"Master prompt template not found: '{self._master_prompt_path}'.")
        if not self._master_prompt_path.is_file():
            raise MasterCasePromptError(
                f"Master prompt template path is not a file: '{self._master_prompt_path}'."
            )

    def _discover_existing_case_ids(self) -> set[str]:
        """Collect case IDs already present beneath the output directory."""

        existing_case_ids: set[str] = set()
        for candidate in self._output_directory.rglob("master_case.json"):
            try:
                payload = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                logger.warning("Skipping unreadable existing case file '%s': %s", candidate, exc)
                continue

            if not isinstance(payload, dict):
                continue

            case_information = payload.get("case_information")
            if not isinstance(case_information, dict):
                continue

            case_id = case_information.get("case_id")
            if isinstance(case_id, str) and case_id.strip():
                existing_case_ids.add(case_id.strip())

        return existing_case_ids

    @staticmethod
    def _serialize_for_prompt(value: Any) -> str:
        """Convert prompt values into a stable string representation."""

        if isinstance(value, str):
            return value
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, (dict, list, tuple, set)):
            return json.dumps(value, indent=2, ensure_ascii=False, default=str)
        return str(value)

    def load_reference_data(self) -> dict[str, Any]:
        """Load and cache all reference datasets required by the master prompt."""

        if self._reference_data_cache is not None:
            return self._reference_data_cache

        reference_data: dict[str, Any] = {
            "names": self._reference_loader.load_directory("dataset/reference_data/names"),
            "locations": self._reference_loader.load_directory("dataset/reference_data/locations"),
            "police": self._reference_loader.load_directory("dataset/reference_data/police"),
            "medical": self._reference_loader.load_directory("dataset/reference_data/medical"),
            "legal": self._reference_loader.load_directory("dataset/reference_data/legal"),
        }

        self._reference_data_cache = reference_data
        logger.debug("Loaded reference data for master case generation.")
        return reference_data

    def build_prompt_context(self, case_seed: Mapping[str, Any]) -> dict[str, str]:
        """Build the template context used to render the master prompt."""

        normalized_seed = {key.upper(): self._serialize_for_prompt(value) for key, value in case_seed.items()}
        prompt_context: dict[str, str] = {
            "SCHEMA": self._schema_json,
            "REFERENCE_DATA": json.dumps(self.load_reference_data(), indent=2, ensure_ascii=False, default=str),
        }
        prompt_context.update(normalized_seed)
        return prompt_context

    def _render_prompt(self, case_seed: Mapping[str, Any]) -> str:
        """Load the master prompt and render it with the supplied context."""

        prompt_template = self._gemini_client.load_prompt_template(self._master_prompt_path)
        prompt_context = self.build_prompt_context(case_seed)
        rendered_prompt = self._gemini_client.render_prompt(prompt_template, prompt_context)

        unresolved_placeholders = sorted({match.group(1) for match in self._PLACEHOLDER_PATTERN.finditer(rendered_prompt)})
        if unresolved_placeholders:
            raise MasterCasePromptError(
                "Unresolved placeholders remain in the rendered prompt: " + ", ".join(unresolved_placeholders)
            )

        return rendered_prompt

    def validate_case(self, raw_json: str) -> MasterCase:
        """Validate raw JSON against the MasterCase schema and enforce ID uniqueness."""

        try:
            validated_case = MasterCase.model_validate_json(raw_json)
        except ValidationError as exc:
            raise MasterCaseValidationError("Generated JSON did not validate as MasterCase.") from exc

        case_id = validated_case.case_information.case_id
        if case_id in self._seen_case_ids:
            raise MasterCaseValidationError(f"Duplicate case_id generated: '{case_id}'.")

        return validated_case

    def save_case(self, case: MasterCase) -> Path:
        """Persist the canonical master_case.json file and return its path."""

        output_path = self._output_directory / "master_case.json"
        try:
            output_path.write_text(case.model_dump_json(indent=2), encoding="utf-8")
        except OSError as exc:
            raise MasterCaseSaveError(f"Failed to save master case to '{output_path}': {exc}") from exc

        self._seen_case_ids.add(case.case_information.case_id)
        logger.info("Saved master case to %s", output_path)
        return output_path

    def generate_case(self, case_seed: Mapping[str, Any]) -> MasterCase:
        """Generate, validate, and persist one canonical master case.

        The caller supplies the template seed values used to render the master
        prompt. Validation failures trigger retries up to the configured limit.
        """

        last_validation_error: MasterCaseValidationError | None = None

        for attempt in range(1, self._validation_retries + 1):
            rendered_prompt = self._render_prompt(case_seed)

            try:
                raw_json = self._gemini_client.send_prompt(rendered_prompt)
                validated_case = self.validate_case(raw_json)
            except GeminiRequestError:
                raise
            except GeminiTemplateError as exc:
                raise MasterCasePromptError(str(exc)) from exc
            except MasterCaseValidationError as exc:
                last_validation_error = exc
                logger.error(
                    "MasterCase validation failed on attempt %s/%s: %s",
                    attempt,
                    self._validation_retries,
                    exc,
                )
                if attempt < self._validation_retries:
                    continue
                break

            self.save_case(validated_case)
            return validated_case

        if last_validation_error is not None:
            raise last_validation_error

        raise MasterCaseGenerationError("Master case generation failed for an unknown reason.")

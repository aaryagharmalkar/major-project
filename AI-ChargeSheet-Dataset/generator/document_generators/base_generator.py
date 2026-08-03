"""Abstract base class for deterministic document generators.

Document generators transform a validated MasterCase into document-specific
schemas, render those schemas into Markdown, and save the result to disk.
They do not call an LLM, invent facts, or perform PDF conversion.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Sequence, TypeVar

from pydantic import BaseModel

from generator.renderers.base_renderer import BaseRenderer
from generator.renderers.markdown_renderer import MarkdownRenderer
from generator.schemas.master_case_schema import MasterCase


logger = logging.getLogger(__name__)

DocumentSchemaT = TypeVar("DocumentSchemaT", bound=BaseModel)


class BaseDocumentGenerator(ABC, Generic[DocumentSchemaT]):
    """Template-method base class for all Markdown document generators."""

    document_schema_model: type[DocumentSchemaT]

    def __init__(
        self,
        master_case: MasterCase,
        output_directory: str | Path,
        *,
        renderer: BaseRenderer[Any, str] | None = None,
    ) -> None:
        """Initialize the generator with its validated MasterCase and output path."""

        self._master_case = master_case
        self._output_directory = Path(output_directory).expanduser().resolve()
        self._output_directory.mkdir(parents=True, exist_ok=True)
        self._renderer = renderer or MarkdownRenderer()

    @abstractmethod
    def _build_documents(self) -> Sequence[Any]:
        """Build raw document payloads or schema instances from the MasterCase."""

    @abstractmethod
    def _output_filename(self, document: DocumentSchemaT, index: int) -> str:
        """Return the filename used to persist the rendered Markdown document."""

    def validate(self, document: Any) -> DocumentSchemaT:
        """Validate a raw document payload using the document schema model."""

        return self.document_schema_model.model_validate(document)

    def render(self, document: DocumentSchemaT) -> str:
        """Render a validated document schema into Markdown."""

        return self._renderer.render(document)

    def save(self, content: str, filename: str) -> Path:
        """Save rendered Markdown content to the output directory."""

        output_path = self._output_directory / filename
        output_path.write_text(content, encoding="utf-8")
        logger.info("Saved document: %s", output_path)
        return output_path

    def generate(self) -> list[Path]:
        """Generate, validate, render, and save all documents for the case."""

        outputs: list[Path] = []
        for index, raw_document in enumerate(self._build_documents(), start=1):
            validated_document = self.validate(raw_document)
            markdown = self.render(validated_document)
            output_path = self.save(markdown, self._output_filename(validated_document, index))
            outputs.append(output_path)
        return outputs

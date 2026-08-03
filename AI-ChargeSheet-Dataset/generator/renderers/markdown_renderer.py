"""Markdown renderer for Pydantic document schemas."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel

from generator.renderers.base_renderer import BaseRenderer


class MarkdownRenderer(BaseRenderer[BaseModel, str]):
    """Render Pydantic document schemas into human-readable Markdown."""

    _SNAKE_CASE_PATTERN = re.compile(r"_+")

    def render(self, value: BaseModel) -> str:
        """Render a validated Pydantic model to Markdown."""

        title = self._document_title(value)
        lines = [f"# {title}", ""]
        lines.extend(self._render_model(value, level=2))
        return "\n".join(line for line in lines if line is not None).rstrip() + "\n"

    def _document_title(self, value: BaseModel) -> str:
        """Derive the top-level document title from the model."""

        document_type = getattr(value, "document_type", None)
        if isinstance(document_type, str) and document_type.strip():
            return document_type.strip()
        return self._humanize(value.__class__.__name__)

    def _render_model(self, model: BaseModel, *, level: int) -> list[str]:
        """Render all fields of a Pydantic model recursively."""

        lines: list[str] = []
        for field_name in model.__class__.model_fields:
            if field_name == "document_type":
                continue

            field_value = getattr(model, field_name)
            heading = self._humanize(field_name)
            lines.append(f"{'#' * level} {heading}")
            lines.extend(self._render_value(field_value, level + 1))
            lines.append("")
        return lines

    def _render_value(self, value: Any, level: int) -> list[str]:
        """Render a single value, preserving nested structure where needed."""

        if value is None:
            return ["- Not provided"]

        if isinstance(value, BaseModel):
            return self._render_model(value, level=level)

        if isinstance(value, Mapping):
            lines: list[str] = []
            for key, nested_value in value.items():
                lines.append(f"{'#' * level} {self._humanize(str(key))}")
                lines.extend(self._render_value(nested_value, level + 1))
                lines.append("")
            return lines or ["- Not provided"]

        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            if not value:
                return ["- None"]

            lines = []
            for index, item in enumerate(value, start=1):
                if isinstance(item, BaseModel):
                    lines.append(f"{'#' * level} Item {index}")
                    lines.extend(self._render_model(item, level=level + 1))
                elif isinstance(item, Mapping):
                    lines.append(f"{'#' * level} Item {index}")
                    lines.extend(self._render_value(item, level + 1))
                else:
                    lines.append(f"- {item}")
                lines.append("")
            return lines

        return [f"- {value}"]

    def _humanize(self, value: str) -> str:
        """Convert snake_case and class names into a human-readable heading."""

        value = self._SNAKE_CASE_PATTERN.sub(" ", value)
        value = re.sub(r"(?<!^)(?=[A-Z])", " ", value).strip()
        return value.replace("FIR", "FIR").replace("FSL", "FSL").title()

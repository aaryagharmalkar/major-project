"""Abstract base class for PDF rendering operations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BasePDFRenderer(ABC, Generic[InputT, OutputT]):
    """Base interface for rendering content into PDF-compatible outputs."""

    @abstractmethod
    def render(self, value: InputT) -> OutputT:
        """Render the provided input into the renderer's output format."""

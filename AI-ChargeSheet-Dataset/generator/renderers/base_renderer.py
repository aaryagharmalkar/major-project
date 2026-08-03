"""Abstract renderer interfaces used by the document generation layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseRenderer(ABC, Generic[InputT, OutputT]):
    """Abstract renderer contract for transforming structured data."""

    @abstractmethod
    def render(self, value: InputT) -> OutputT:
        """Render the provided value into the renderer's output type."""

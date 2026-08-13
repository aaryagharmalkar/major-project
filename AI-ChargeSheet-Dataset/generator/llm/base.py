"""
Abstract LLM client used by every provider.

Every concrete implementation (Gemini, OpenRouter, Groq, OpenAI, etc.)
inherits from BaseLLMClient so the rest of the project never depends on
a specific provider.
"""

from __future__ import annotations

import abc
import json
import logging
import os
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ==========================================================
# Exceptions
# ==========================================================


class LLMClientError(Exception):
    """Base exception for all LLM client failures."""


class LLMConfigurationError(LLMClientError):
    """Raised when an LLM client cannot be configured."""


class LLMTemplateError(LLMClientError):
    """Raised when prompt loading/rendering fails."""


class LLMRequestError(LLMClientError):
    """Raised when an API request fails."""


class LLMResponseError(LLMClientError):
    """Raised when the provider returns an invalid response."""


# ==========================================================
# Base Client
# ==========================================================


class BaseLLMClient(abc.ABC):
    """
    Abstract base class for every LLM provider.

    Handles:

    - prompt loading
    - prompt rendering
    - placeholder replacement
    - environment loading
    - markdown fence stripping

    Does NOT implement:

    - network requests
    - provider-specific payloads
    - response parsing
    """

    PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")
    FENCE_PATTERN = re.compile(
        r"^```(?:json)?\s*|\s*```$",
        re.IGNORECASE | re.DOTALL,
    )

    def __init__(
        self,
        *,
        api_key: str | None,
        model: str,
        timeout_seconds: float = 120,
        max_retries: int = 3,
        prompt_encoding: str = "utf-8",
    ) -> None:

        if not api_key:
            raise LLMConfigurationError(
                "Missing API key."
            )

        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.prompt_encoding = prompt_encoding

    # ======================================================
    # Prompt Loading
    # ======================================================

    def load_prompt_template(
        self,
        template_path: str | Path,
    ) -> str:

        path = Path(template_path).expanduser().resolve()

        if not path.exists():
            raise LLMTemplateError(
                f"Prompt template not found: {path}"
            )

        try:
            template = path.read_text(
                encoding=self.prompt_encoding
            )
        except OSError as exc:
            raise LLMTemplateError(str(exc)) from exc

        if not template.strip():
            raise LLMTemplateError(
                "Prompt template is empty."
            )

        return template

    # ======================================================
    # Prompt Rendering
    # ======================================================

    @staticmethod
    def _normalize_variables(
        variables: Mapping[str, Any] | None,
    ) -> dict[str, str]:

        if not variables:
            return {}

        normalized: dict[str, str] = {}

        for key, value in variables.items():

            if value is None:
                normalized[key] = ""

            elif isinstance(value, str):
                normalized[key] = value

            elif isinstance(value, (dict, list, tuple, set)):
                normalized[key] = json.dumps(
                    value,
                    indent=2,
                    ensure_ascii=False,
                    default=str,
                )

            else:
                normalized[key] = str(value)

        return normalized

    def render_prompt(
        self,
        template: str,
        variables: Mapping[str, Any] | None = None,
    ) -> str:

        values = self._normalize_variables(variables)

        def replace(match: re.Match[str]) -> str:

            name = match.group(1)

            return values.get(name, match.group(0))

        rendered = self.PLACEHOLDER_PATTERN.sub(
            replace,
            template,
        )

        if not rendered.strip():
            raise LLMTemplateError(
                "Rendered prompt is empty."
            )

        return rendered

    # ======================================================
    # Helpers
    # ======================================================

    @classmethod
    def strip_markdown_code_fences(
        cls,
        text: str,
    ) -> str:

        text = text.strip()

        if not text:
            return text

        if text.startswith("```"):

            lines = text.splitlines()

            if len(lines) >= 2 and lines[-1].strip() == "```":

                return "\n".join(lines[1:-1]).strip()

        return cls.FENCE_PATTERN.sub("", text).strip()

    # ======================================================
    # Abstract Interface
    # ======================================================

    @abc.abstractmethod
    def send_prompt(
        self,
        prompt: str,
    ) -> str:
        """
        Send a prompt to the provider.

        Must return ONLY the model text.
        """

    @abc.abstractmethod
    def health_check(
        self,
    ) -> bool:
        """
        Verify the provider is reachable.
        """

    # ======================================================
    # Convenience
    # ======================================================

    def generate_from_template(
        self,
        template_path: str | Path,
        variables: Mapping[str, Any] | None = None,
    ) -> str:

        template = self.load_prompt_template(
            template_path
        )

        prompt = self.render_prompt(
            template,
            variables,
        )

        return self.send_prompt(prompt)
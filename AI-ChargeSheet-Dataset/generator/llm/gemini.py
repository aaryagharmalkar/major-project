"""Standalone Gemini API client.

This module intentionally contains no domain knowledge. It only loads prompt
templates, expands placeholders, sends the resulting prompt to Gemini, and
returns the raw text response.
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
from typing import Any
from urllib import error, request


logger = logging.getLogger(__name__)


class GeminiClientError(Exception):
    """Base exception for Gemini client failures."""


class GeminiConfigurationError(GeminiClientError):
    """Raised when the client cannot be configured correctly."""


class GeminiTemplateError(GeminiClientError):
    """Raised when a prompt template cannot be loaded or rendered."""


class GeminiRequestError(GeminiClientError):
    """Raised when a request to Gemini fails after retries are exhausted."""


class GeminiResponseError(GeminiClientError):
    """Raised when Gemini returns an empty or unusable response."""


@dataclass(frozen=True, slots=True)
class GeminiResponseConfig:
    """Response-generation settings for the Gemini REST API."""

    temperature: float = 0.2
    top_p: float = 0.95
    top_k: int = 40
    max_output_tokens: int = 8192
    response_mime_type: str = "application/json"


class GeminiClient:
    """Thin Gemini REST client with template loading and retry handling."""

    _FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.DOTALL)
    _PLACEHOLDER_PATTERN = re.compile(r"{{\s*([A-Z0-9_]+)\s*}}")

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        api_base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout_seconds: float = 60.0,
        max_retries: int = 3,
        retry_initial_delay_seconds: float = 1.0,
        retry_backoff_factor: float = 2.0,
        prompt_encoding: str = "utf-8",
    ) -> None:
        """Initialize the Gemini client.

        Args:
            api_key: Gemini API key. If omitted, it is loaded from GEMINI_API_KEY.
            model: Gemini model name.
            api_base_url: Base REST endpoint for the Gemini API.
            timeout_seconds: HTTP timeout for each request.
            max_retries: Maximum number of attempts for transient failures.
            retry_initial_delay_seconds: Initial delay before retrying.
            retry_backoff_factor: Multiplier applied after each failed attempt.
            prompt_encoding: Encoding used when reading template files.
        """

        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not resolved_api_key:
            raise GeminiConfigurationError(
                "Missing Gemini API key. Set the GEMINI_API_KEY environment variable or pass api_key explicitly."
            )

        if max_retries < 1:
            raise GeminiConfigurationError("max_retries must be at least 1.")

        if timeout_seconds <= 0:
            raise GeminiConfigurationError("timeout_seconds must be greater than zero.")

        self._api_key = resolved_api_key
        self._model = model.strip()
        self._api_base_url = api_base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._max_retries = max_retries
        self._retry_initial_delay_seconds = retry_initial_delay_seconds
        self._retry_backoff_factor = retry_backoff_factor
        self._prompt_encoding = prompt_encoding
        self._response_config = GeminiResponseConfig()

    @staticmethod
    def _normalize_template_variables(template_variables: Mapping[str, Any] | None) -> dict[str, str]:
        """Convert template variables to string values for placeholder expansion."""

        if not template_variables:
            return {}

        return {key: "" if value is None else str(value) for key, value in template_variables.items()}

    def load_prompt_template(self, template_path: str | Path) -> str:
        """Load a prompt template from disk.

        Args:
            template_path: Path to the prompt template file.

        Returns:
            The template text.

        Raises:
            GeminiTemplateError: If the file cannot be read or is empty.
        """

        path = Path(template_path).expanduser().resolve()
        if not path.exists():
            raise GeminiTemplateError(f"Prompt template not found: '{path}'.")
        if not path.is_file():
            raise GeminiTemplateError(f"Prompt template path is not a file: '{path}'.")

        try:
            template = path.read_text(encoding=self._prompt_encoding)
        except OSError as exc:
            raise GeminiTemplateError(f"Failed to read prompt template '{path}': {exc}") from exc

        if not template.strip():
            raise GeminiTemplateError(f"Prompt template is empty: '{path}'.")

        return template

    def render_prompt(self, template: str, template_variables: Mapping[str, Any] | None = None) -> str:
        """Replace template placeholders using double-brace syntax.

        Missing placeholders are left untouched so callers can detect incomplete
        templates before sending a request.
        """

        variables = self._normalize_template_variables(template_variables)

        def replace_placeholder(match: re.Match[str]) -> str:
            placeholder_name = match.group(1)
            return variables.get(placeholder_name, match.group(0))

        rendered = self._PLACEHOLDER_PATTERN.sub(replace_placeholder, template)
        if not rendered.strip():
            raise GeminiTemplateError("Rendered prompt is empty.")
        return rendered

    @classmethod
    def strip_markdown_code_fences(cls, text: str) -> str:
        """Remove surrounding markdown code fences from a model response."""

        stripped = text.strip()
        if not stripped:
            return stripped

        if stripped.startswith("```"):
            lines = stripped.splitlines()
            if len(lines) >= 2 and lines[-1].strip() == "```":
                body = "\n".join(lines[1:-1]).strip()
                return body

        return cls._FENCE_PATTERN.sub("", stripped).strip()

    def _build_request_payload(self, prompt: str) -> dict[str, Any]:
        """Build the Gemini REST request body."""

        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": self._response_config.temperature,
                "topP": self._response_config.top_p,
                "topK": self._response_config.top_k,
                "maxOutputTokens": self._response_config.max_output_tokens,
                "responseMimeType": self._response_config.response_mime_type,
            },
        }

    def _request_url(self) -> str:
        """Build the model-specific REST URL."""

        return f"{self._api_base_url}/models/{self._model}:generateContent?key={self._api_key}"

    @staticmethod
    def _is_transient_error(exc: Exception) -> bool:
        """Determine whether a failure should be retried."""

        if isinstance(exc, error.HTTPError):
            return exc.code in {408, 429, 500, 502, 503, 504}
        if isinstance(exc, error.URLError):
            return True
        if isinstance(exc, TimeoutError):
            return True
        return False

    @staticmethod
    def _extract_response_text(response_payload: Mapping[str, Any]) -> str:
        """Extract the first text part from a Gemini response payload."""

        candidates = response_payload.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise GeminiResponseError("Gemini response did not contain any candidates.")

        for candidate in candidates:
            if not isinstance(candidate, Mapping):
                continue
            content = candidate.get("content")
            if not isinstance(content, Mapping):
                continue
            parts = content.get("parts")
            if not isinstance(parts, list):
                continue
            for part in parts:
                if isinstance(part, Mapping):
                    text = part.get("text")
                    if isinstance(text, str) and text.strip():
                        return text

        raise GeminiResponseError("Gemini response did not contain any text content.")

    def send_prompt(self, prompt: str) -> str:
        """Send a completed prompt to Gemini and return the raw JSON string.

        Raises:
            GeminiRequestError: If the request repeatedly fails.
            GeminiResponseError: If Gemini responds without usable text.
        """

        if not prompt or not prompt.strip():
            raise GeminiTemplateError("Prompt is empty.")

        payload = json.dumps(self._build_request_payload(prompt)).encode("utf-8")
        url = self._request_url()
        request_headers = {
            "Content-Type": "application/json; charset=utf-8",
        }

        delay = self._retry_initial_delay_seconds
        last_error: Exception | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                http_request = request.Request(url=url, data=payload, headers=request_headers, method="POST")
                with request.urlopen(http_request, timeout=self._timeout_seconds) as http_response:
                    raw_body = http_response.read().decode("utf-8")

                if not raw_body.strip():
                    raise GeminiResponseError("Gemini returned an empty response body.")

                response_payload = json.loads(raw_body)
                response_text = self._extract_response_text(response_payload)
                cleaned_text = self.strip_markdown_code_fences(response_text)

                if not cleaned_text.strip():
                    raise GeminiResponseError("Gemini returned an empty text payload.")

                logger.debug("Gemini request succeeded on attempt %s", attempt)
                return cleaned_text

            except GeminiClientError:
                raise
            except Exception as exc:  # noqa: BLE001 - deliberate boundary around network calls
                last_error = exc
                if attempt >= self._max_retries or not self._is_transient_error(exc):
                    break

                jitter = random.uniform(0.0, 0.25 * delay)
                sleep_for = delay + jitter
                logger.warning(
                    "Gemini request failed on attempt %s/%s; retrying in %.2f seconds: %s",
                    attempt,
                    self._max_retries,
                    sleep_for,
                    exc,
                )
                time.sleep(sleep_for)
                delay *= self._retry_backoff_factor

        if isinstance(last_error, GeminiResponseError):
            raise last_error

        raise GeminiRequestError(
            f"Gemini request failed after {self._max_retries} attempts: {last_error}"
        ) from last_error

    def load_and_render_prompt(
        self,
        template_path: str | Path,
        template_variables: Mapping[str, Any] | None = None,
    ) -> str:
        """Convenience helper to load a template and render it in one step."""

        template = self.load_prompt_template(template_path)
        return self.render_prompt(template, template_variables)

    def generate_from_template(
        self,
        template_path: str | Path,
        template_variables: Mapping[str, Any] | None = None,
    ) -> str:
        """Load, render, and send a prompt template to Gemini.

        Returns only the raw JSON string emitted by the model.
        """

        prompt = self.load_and_render_prompt(template_path, template_variables)
        return self.send_prompt(prompt)

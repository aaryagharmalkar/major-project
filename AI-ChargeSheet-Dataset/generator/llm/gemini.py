"""
Gemini implementation of BaseLLMClient.

Only contains Gemini-specific logic.

Everything else (prompt loading, rendering, template handling,
markdown stripping, etc.) comes from BaseLLMClient.
"""

from __future__ import annotations

import json
import logging
import os
import random
import time
from collections.abc import Mapping
from typing import Any
from urllib import error, request

from generator.llm.base import (
    BaseLLMClient,
    LLMConfigurationError,
    LLMRequestError,
    LLMResponseError,
)

logger = logging.getLogger(__name__)


class GeminiClient(BaseLLMClient):
    """Google Gemini implementation."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 120,
        max_retries: int = 3,
    ) -> None:

        api_key = api_key or os.getenv("GEMINI_API_KEY")

        model = model or os.getenv(
            "GEMINI_MODEL",
            "gemini-2.0-flash",
        )

        if not api_key:
            raise LLMConfigurationError(
                "Missing GEMINI_API_KEY."
            )

        super().__init__(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    # ---------------------------------------------------------

    def _request_url(self) -> str:

        return (
            f"{self.BASE_URL}"
            f"/models/{self.model}:generateContent"
            f"?key={self.api_key}"
        )

    # ---------------------------------------------------------

    def _payload(
        self,
        prompt: str,
    ) -> dict[str, Any]:

        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 8192,
                "responseMimeType": "application/json",
            },
        }

    # ---------------------------------------------------------

    @staticmethod
    def _extract_text(
        payload: Mapping[str, Any],
    ) -> str:

        candidates = payload.get("candidates")

        if not candidates:
            raise LLMResponseError(
                "No Gemini candidates."
            )

        return (
            candidates[0]
            ["content"]
            ["parts"][0]
            ["text"]
        )

    # ---------------------------------------------------------

    @staticmethod
    def _retryable(
        exc: Exception,
    ) -> bool:

        if isinstance(exc, error.HTTPError):

            return exc.code in {
                408,
                429,
                500,
                502,
                503,
                504,
            }

        if isinstance(exc, error.URLError):
            return True

        if isinstance(exc, TimeoutError):
            return True

        return False

    # ---------------------------------------------------------

    def send_prompt(
        self,
        prompt: str,
    ) -> str:

        payload = json.dumps(
            self._payload(prompt)
        ).encode("utf-8")

        delay = 1.0
        last_error = None

        for attempt in range(
            1,
            self.max_retries + 1,
        ):

            try:

                req = request.Request(
                    self._request_url(),
                    data=payload,
                    headers={
                        "Content-Type":
                        "application/json"
                    },
                    method="POST",
                )

                with request.urlopen(
                    req,
                    timeout=self.timeout_seconds,
                ) as response:

                    body = response.read().decode()

                payload = json.loads(body)

                text = self._extract_text(payload)

                text = self.strip_markdown_code_fences(
                    text
                )

                if not text.strip():

                    raise LLMResponseError(
                        "Empty Gemini response."
                    )

                logger.info(
                    "Gemini request succeeded."
                )

                return text

            except Exception as exc:

                last_error = exc

                if (
                    attempt == self.max_retries
                    or not self._retryable(exc)
                ):
                    break

                sleep = (
                    delay
                    + random.random()
                )

                logger.warning(
                    "Retry %s/%s in %.2f sec",
                    attempt,
                    self.max_retries,
                    sleep,
                )

                time.sleep(sleep)

                delay *= 2

        raise LLMRequestError(
            str(last_error)
        )

    # ---------------------------------------------------------

    def health_check(
        self,
    ) -> bool:

        try:

            req = request.Request(
                self._request_url(),
                data=json.dumps(
                    self._payload("hello")
                ).encode(),
                headers={
                    "Content-Type":
                    "application/json"
                },
                method="POST",
            )

            with request.urlopen(
                req,
                timeout=10,
            ):

                return True

        except Exception:

            return False
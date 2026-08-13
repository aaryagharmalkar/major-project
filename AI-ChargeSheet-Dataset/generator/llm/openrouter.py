"""
OpenRouter LLM client.

Implements BaseLLMClient using the OpenRouter Chat Completions API.

Compatible with:

- Qwen
- DeepSeek
- Llama
- Mistral
- GPT
- Claude
"""

from __future__ import annotations

import json
import logging
import os
import random
import time

import httpx

from generator.llm.base import (
    BaseLLMClient,
    LLMConfigurationError,
    LLMRequestError,
    LLMResponseError,
)

logger = logging.getLogger(__name__)


class OpenRouterClient(BaseLLMClient):
    """OpenRouter implementation of BaseLLMClient."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = 120,
        max_retries: int = 3,
    ) -> None:

        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        model = model or os.getenv(
            "OPENROUTER_MODEL",
            "qwen/qwen3-235b-a22b"
        )

        if not api_key:
            raise LLMConfigurationError(
                "OPENROUTER_API_KEY not found."
            )

        super().__init__(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )

    # --------------------------------------------------

    def _headers(self) -> dict[str, str]:

        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com",
            "X-Title": "AI-ChargeSheet-Dataset",
        }

    # --------------------------------------------------

    def _payload(
        self,
        prompt: str,
    ) -> dict:

        return {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "temperature": 0.2,
            "response_format": {
                "type": "json_object"
            },
        }

    # --------------------------------------------------

    def send_prompt(
        self,
        prompt: str,
    ) -> str:

        delay = 1.0
        last_error = None

        for attempt in range(1, self.max_retries + 1):

            try:

                response = httpx.post(
                    self.BASE_URL,
                    headers=self._headers(),
                    json=self._payload(prompt),
                    timeout=self.timeout_seconds,
                )

                response.raise_for_status()

                payload = response.json()

                content = (
                    payload["choices"][0]
                    ["message"]
                    ["content"]
                )

                content = self.strip_markdown_code_fences(
                    content
                )

                if not content.strip():
                    raise LLMResponseError(
                        "Model returned empty response."
                    )

                logger.info(
                    "OpenRouter request succeeded."
                )

                return content

            except Exception as exc:

                last_error = exc

                if attempt == self.max_retries:
                    break

                sleep = delay + random.random()

                logger.warning(
                    "Retry %s/%s in %.2f sec",
                    attempt,
                    self.max_retries,
                    sleep,
                )

                time.sleep(sleep)

                delay *= 2

        raise LLMRequestError(str(last_error))

    # --------------------------------------------------

    def health_check(self) -> bool:

        try:

            response = httpx.get(
                "https://openrouter.ai/api/v1/models",
                timeout=10,
            )

            return response.status_code == 200

        except Exception:

            return False
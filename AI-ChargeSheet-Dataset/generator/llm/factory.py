"""
LLM Factory.

Creates the appropriate LLM client based on configuration.

Supported providers:

- Gemini
- OpenRouter
- Groq (future)
"""

from __future__ import annotations

import os

from generator.llm.base import (
    BaseLLMClient,
    LLMConfigurationError,
)

from generator.llm.gemini import GeminiClient
from generator.llm.openrouter import OpenRouterClient


class LLMFactory:
    """Factory for constructing LLM providers."""

    @staticmethod
    def create(
        provider: str | None = None,
    ) -> BaseLLMClient:
        """
        Create an LLM client.

        Priority:

        1. Explicit provider argument
        2. LLM_PROVIDER environment variable
        """

        provider = (
            provider
            or os.getenv("LLM_PROVIDER", "openrouter")
        ).lower()

        if provider == "gemini":
            return GeminiClient()

        if provider == "openrouter":
            return OpenRouterClient()

        if provider == "groq":
            raise NotImplementedError(
                "Groq client not implemented yet."
            )

        raise LLMConfigurationError(
            f"Unknown LLM provider: '{provider}'"
        )

    @staticmethod
    def supported_providers() -> list[str]:
        """Return supported providers."""

        return [
            "gemini",
            "openrouter",
            "groq",
        ]
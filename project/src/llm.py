from abc import ABC, abstractmethod
from typing import Optional

from .config import Config


class LLMGenerationError(RuntimeError):
    """Raised when the provider returns an incomplete or unusable response."""


class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text from the given prompt."""


class GroqClient(LLMClient):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GROQ_API_KEY
        self.model = model or Config.GROQ_MODEL
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set")
        try:
            from groq import Groq

            self.client = Groq(api_key=self.api_key)
        except ImportError as exc:
            raise ImportError("groq package not installed. Run: pip install groq") from exc

    def generate(self, prompt: str) -> str:
        request_kwargs = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only a valid JSON object. "
                        "Do not add markdown, commentary, or code fences."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
            "max_tokens": 8192,
            "top_p": 0.9,
            "response_format": {"type": "json_object"},
        }

        try:
            response = self.client.chat.completions.create(**request_kwargs)
        except Exception:
            # Fallback for models/providers that do not support JSON mode.
            request_kwargs.pop("response_format", None)
            try:
                response = self.client.chat.completions.create(**request_kwargs)
            except Exception as exc:
                raise RuntimeError(f"Groq API call failed: {exc}") from exc

        choice = response.choices[0]
        content = choice.message.content or ""
        finish_reason = getattr(choice, "finish_reason", None)

        if not content.strip():
            raise LLMGenerationError("Groq returned an empty response.")
        if finish_reason == "length":
            raise LLMGenerationError(
                "Groq response was truncated because it hit the token limit."
            )

        return content


class GeminiClient(LLMClient):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        self.model = model or Config.GEMINI_MODEL
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set")
        try:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        except ImportError as exc:
            raise ImportError(
                "google-generativeai package not installed. "
                "Run: pip install google-generativeai"
            ) from exc

    def generate(self, prompt: str) -> str:
        generation_config = {
            "temperature": 0.2,
            "max_output_tokens": 8192,
            "response_mime_type": "application/json",
        }

        try:
            response = self.client.generate_content(
                prompt,
                generation_config=generation_config,
            )
        except Exception as exc:
            raise RuntimeError(f"Gemini API call failed: {exc}") from exc

        content = getattr(response, "text", "") or ""
        candidates = getattr(response, "candidates", None) or []
        finish_reason = getattr(candidates[0], "finish_reason", None) if candidates else None

        if not content.strip():
            raise LLMGenerationError("Gemini returned an empty response.")
        if str(finish_reason).upper() == "MAX_TOKENS":
            raise LLMGenerationError(
                "Gemini response was truncated because it hit the token limit."
            )

        return content


def get_llm_client() -> LLMClient:
    provider = Config.LLM_PROVIDER
    if provider == "groq":
        return GroqClient()
    if provider == "gemini":
        return GeminiClient()
    raise ValueError(f"Unsupported provider: {provider}")

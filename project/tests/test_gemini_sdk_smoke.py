"""Opt-in live SDK smoke test; excluded from normal automated test runs."""

import os

import pytest


@pytest.mark.skipif(
    os.getenv("RUN_GEMINI_SMOKE") != "1" or not os.getenv("GEMINI_API_KEY"),
    reason="Set RUN_GEMINI_SMOKE=1 and GEMINI_API_KEY to run the live Gemini SDK smoke test.",
)
def test_google_genai_text_generation_smoke() -> None:
    """Proves the configured account/model can generate without exposing credentials."""
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-flash-latest"),
        contents="Reply with exactly: BYOMKESH_SMOKE_OK",
        config={"temperature": 0},
    )
    assert "BYOMKESH_SMOKE_OK" in (response.text or "")

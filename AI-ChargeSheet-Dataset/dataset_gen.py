"""Run one synthetic Pune robbery master-case generation from the terminal."""

from __future__ import annotations

import os
from pathlib import Path

from generator.case_generator import MasterCaseGenerator
from generator.llm.gemini import GeminiClient
from generator.utils.reference_loader import ReferenceDataLoader


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_PATH = PROJECT_ROOT / ".env"
OUTPUT_DIRECTORY = PROJECT_ROOT / "dataset" / "synthetic" / "CASE_001"

CASE_SEED = {
    "crime_category": "Robbery",
    "state": "Maharashtra",
    "district": "Pune",
    "location": "Pune city",
    "investigation_style": (
        "Medium difficulty; one victim, two accused, and three witnesses; "
        "include medical examination, forensic report, seizure memo, arrest memo, "
        "spot panchanama, case diary, and charge sheet."
    ),
    "case_outcome": "Charge sheet filed",
}


def load_gemini_api_key() -> None:
    """Load GEMINI_API_KEY from the local .env file without extra dependencies."""

    if not ENV_PATH.is_file():
        raise FileNotFoundError(f"Missing environment file: {ENV_PATH}")

    for line in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() == "GEMINI_API_KEY" and value.strip():
            os.environ["GEMINI_API_KEY"] = value.strip().strip('"').strip("'")
            return

    raise RuntimeError("GEMINI_API_KEY is missing or empty in .env.")


def main() -> None:
    load_gemini_api_key()

    generator = MasterCaseGenerator(
        reference_loader=ReferenceDataLoader(PROJECT_ROOT),
        gemini_client=GeminiClient(),
        master_prompt_path=PROJECT_ROOT / "generator" / "prompts" / "master_case.md",
        output_directory=OUTPUT_DIRECTORY,
    )
    master_case = generator.generate_case(CASE_SEED)

    print(f"Generated {master_case.case_information.case_id}")
    print(f"Saved: {OUTPUT_DIRECTORY / 'master_case.json'}")


if __name__ == "__main__":
    main()

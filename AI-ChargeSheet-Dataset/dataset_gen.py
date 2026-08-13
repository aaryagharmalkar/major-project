"""
Run one synthetic criminal investigation case generation.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from generator.case_generator import MasterCaseGenerator
from generator.llm.factory import LLMFactory
from generator.utils.reference_loader import ReferenceDataLoader

# ==========================================================
# Paths
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent

load_dotenv(PROJECT_ROOT / ".env")

OUTPUT_DIRECTORY = (
    PROJECT_ROOT
    / "dataset"
    / "synthetic"
    / "CASE_001"
)

# ==========================================================
# Seed
# ==========================================================

CASE_SEED = {
    "crime_category": "Robbery",
    "state": "Maharashtra",
    "district": "Pune",
    "location": "Pune City",
    "investigation_style": (
        "Medium difficulty; one victim, two accused, "
        "three witnesses; include seizure memo, "
        "medical report, FSL report, arrest memo, "
        "case diary and final charge sheet."
    ),
    "case_outcome": "Charge sheet filed",
}

# ==========================================================
# Main
# ==========================================================


def main() -> None:

    provider = os.getenv(
        "LLM_PROVIDER",
        "openrouter",
    )

    print(f"Using LLM Provider : {provider}")

    llm_client = LLMFactory.create()

    generator = MasterCaseGenerator(
        reference_loader=ReferenceDataLoader(PROJECT_ROOT),
        llm_client=llm_client,
        master_prompt_path=(
            PROJECT_ROOT
            / "generator"
            / "prompts"
            / "master_case.md"
        ),
        output_directory=OUTPUT_DIRECTORY,
    )

    master_case = generator.generate_case(CASE_SEED)

    print(
        f"\nGenerated Case : "
        f"{master_case.case_information.case_id}"
    )

    print(
        f"Saved to : "
        f"{OUTPUT_DIRECTORY/'master_case.json'}"
    )


if __name__ == "__main__":
    main()
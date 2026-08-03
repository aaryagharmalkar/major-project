"""Convenience entry point for the synthetic case generation workflow."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from generator.llm.gemini import GeminiClient
from generator.case_generator import MasterCaseGenerator
from generator.utils.reference_loader import ReferenceDataLoader


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser for the generator workflow."""

    parser = argparse.ArgumentParser(description="Generate synthetic case data and documents")
    parser.add_argument("--dataset-root", default=".", help="Path to the repository root or dataset root")
    parser.add_argument("--output-dir", default="dataset/synthetic", help="Directory for generated case artifacts")
    parser.add_argument("--master-prompt", default="generator/prompts/master_case.md", help="Path to the master-case prompt template")
    parser.add_argument("--case-seed", default="{}", help="JSON seed for the master-case generation prompt")
    return parser


def main() -> None:
    """Run the generator workflow from the command line."""

    args = build_parser().parse_args()
    dataset_root = Path(args.dataset_root).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    case_seed = {}

    if args.case_seed != "{}":
        import json

        case_seed = json.loads(args.case_seed)

    reference_loader = ReferenceDataLoader(dataset_root)
    gemini_client = GeminiClient(api_key=os.getenv("GEMINI_API_KEY"))
    generator = MasterCaseGenerator(
        reference_loader=reference_loader,
        gemini_client=gemini_client,
        master_prompt_path=args.master_prompt,
        output_directory=output_dir,
    )
    generator.generate_case(case_seed)


if __name__ == "__main__":
    main()

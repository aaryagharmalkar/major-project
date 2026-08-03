# AI Charge Sheet Dataset Generator

This project generates synthetic criminal investigation case data and downstream legal documents from a prompt-driven workflow. The system combines reference data, a Gemini-based generation step, strict schema validation, and document rendering to produce a canonical master case plus Markdown artifacts.

## What the system does

The pipeline currently performs the following steps:

1. Loads reference data from the dataset reference folders such as names, locations, police data, medical data, and legal sections.
2. Builds a master-case generation prompt from a reusable template and a small seed payload.
3. Sends the prompt to Gemini and receives a JSON response.
4. Validates the generated JSON against the Pydantic master-case schema.
5. Saves the validated result as a canonical master case JSON file.
6. Builds document outputs such as FIR and witness statements from the validated master case.

The generated files are stored under the synthetic dataset output area, typically under dataset/synthetic/.

## Project structure

- generator/case_generator.py: orchestrates prompt rendering, validation, and persistence.
- generator/llm/gemini.py: thin Gemini client for prompt submission.
- generator/schemas/: Pydantic schemas for the master case and generated documents.
- generator/document_generators/: generators for FIR and witness documents.
- generator/renderers/: Markdown rendering layer.
- dataset/reference_data/: reusable source dictionaries used to seed the pipeline.

## Prerequisites

- Python 3.10+
- A Gemini API key available as an environment variable named GEMINI_API_KEY
- Internet access for the Gemini API call

## Installation

From the repository root, install the required Python packages:

```bash
pip install pydantic requests
```

If you prefer to keep dependencies in a requirements file, add them to requirements.txt before installing.

## How to run the generator

The entry point is:

```bash
python generator/main.py --help
```

To generate a case, run:

```bash
set GEMINI_API_KEY=your_api_key_here
python generator/main.py --dataset-root . --output-dir dataset/synthetic --master-prompt generator/prompts/master_case.md --case-seed "{}"
```

On PowerShell, the environment variable assignment is:

```powershell
$env:GEMINI_API_KEY="your_api_key_here"
python generator/main.py --dataset-root . --output-dir dataset/synthetic --master-prompt generator/prompts/master_case.md --case-seed "{}"
```

## What gets produced

A typical run creates:

- dataset/synthetic/master_case.json
- Markdown documents such as fir.md and witness_01.md
- Case-specific directories and metadata under the output tree

## How to test it

You can verify that the codebase is valid without calling the API by running:

```bash
python -m compileall generator
```

You can also verify the CLI entry point:

```bash
python generator/main.py --help
```

If you want to test the document generation logic locally, use a small Python snippet that constructs a validated master case object and runs a document generator. The project already supports that flow through the Pydantic schemas and document generator classes.

## Notes

- The full generation path depends on Gemini and therefore requires a valid API key.
- The validation step is strict, so malformed or incomplete outputs will be rejected rather than silently accepted.
- The generator is designed to be deterministic where possible, while still allowing the LLM to fill in case-specific content.

import sys
from pathlib import Path
from .config import Config
from .loader import load_case_data
from .prompt_builder import PromptBuilder
from .llm import get_llm_client
from .pdf_generator import PDFGenerator
from .utils import ensure_directory

def main():
    # Validate config
    try:
        Config.validate()
    except Exception as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file and ensure all required keys are set.")
        sys.exit(1)
    
    # Ensure output directory exists
    output_dir = Path(Config.OUTPUT_DIR).resolve()
    output_pdf = output_dir / "ChargeSheet.pdf"
    ensure_directory(output_dir)
    
    # Load case data
    input_dir = Path(Config.INPUT_DIR).resolve()
    if not input_dir.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        sys.exit(1)
    print(f"Loading case data from {input_dir}...")
    case_data = load_case_data(input_dir)
    print(f"Loaded {len(case_data)} JSON files.")
    
    # Build prompt
    print("Building prompt...")
    prompt = PromptBuilder.build_prompt(case_data)
    
    # Get LLM client
    print(f"Using LLM provider: {Config.LLM_PROVIDER}")
    llm_client = get_llm_client()
    
    # Generate charge sheet
    print("Generating charge sheet via LLM...")
    response = llm_client.generate(prompt)
    print("LLM response received.")
    
    # Generate PDF
    print("Generating PDF...")
    pdf_gen = PDFGenerator()
    pdf_gen.generate_pdf(response, output_pdf)
    print(f"Done. PDF saved to {output_pdf}")

if __name__ == "__main__":
    main()
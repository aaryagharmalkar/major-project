# AI-Powered Charge Sheet Generator

This application reads investigation JSON files, sends the complete case context to an LLM (Groq or Gemini), and generates a professionally formatted Indian Police Charge Sheet as a PDF.

## Setup

 Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt


   
## Explanation

- **Loader**: Reads all `.json` files from the input directory, ignoring errors.
- **Prompt Builder**: Constructs a detailed prompt instructing the LLM to output a strict JSON with the required sections.
- **LLM Client**: Abstracts Groq and Gemini, configurable via `.env`.
- **PDF Generator**: Parses the JSON response and uses ReportLab to create a multi-page PDF with proper formatting, tables, headers, and signatures.
- **Main**: Orchestrates the entire pipeline.

This solution meets all requirements: modular architecture, type hints, error handling, and easy future integration with a RAG pipeline.
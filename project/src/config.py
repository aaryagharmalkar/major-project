import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Provider
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
    
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
    
    # Paths
    INPUT_DIR = os.getenv("INPUT_DIR", "dummy_case")
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
    
    @classmethod
    def validate(cls):
        # Validate provider and API key
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is required when using Groq")
        if cls.LLM_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required when using Gemini")
        if cls.LLM_PROVIDER not in ["groq", "gemini"]:
            raise ValueError(f"Unsupported LLM_PROVIDER: {cls.LLM_PROVIDER}")
        
        # Ensure paths are strings
        if not isinstance(cls.INPUT_DIR, str) or not isinstance(cls.OUTPUT_DIR, str):
            raise TypeError("INPUT_DIR and OUTPUT_DIR must be strings")
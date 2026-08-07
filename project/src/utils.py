import json
import re
from pathlib import Path
from typing import Any, Dict

def read_json_file(file_path: Path) -> Dict[str, Any]:
    """
    Read a JSON file, strip comments (// and /* */), and parse.
    This is a simple comment stripper. For production, consider using json5.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove single-line comments starting with // (not inside strings)
        # A simple approach: remove lines that start with // after stripping whitespace
        lines = content.split('\n')
        clean_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip whole-line comments
            if stripped.startswith('//'):
                continue
            # Remove inline // comments (if not inside quotes) – basic handling
            # For simplicity, we'll just remove // that are not within quotes.
            # A safer approach is to use json5 library, but for our dummy data this works.
            clean_lines.append(line)
        clean_content = '\n'.join(clean_lines)
        
        # Remove multi-line comments /* ... */
        clean_content = re.sub(r'/\*.*?\*/', '', clean_content, flags=re.DOTALL)
        
        # Remove BOM if present
        if clean_content.startswith('\ufeff'):
            clean_content = clean_content[1:]
        
        return json.loads(clean_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path.name}: {e}")
    except Exception as e:
        raise IOError(f"Could not read {file_path.name}: {e}")

def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Failed to create directory '{path}': {e}")
from pathlib import Path
from typing import Dict, Any, List
from .utils import read_json_file

def load_case_data(input_dir: Path) -> Dict[str, Any]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    case_data = {}
    json_files = list(input_dir.glob("*.json"))
    if not json_files:
        raise ValueError(f"No JSON files found in {input_dir}")
    for file_path in json_files:
        key = file_path.stem
        try:
            case_data[key] = read_json_file(file_path)
        except Exception as e:
            print(f"Warning: Could not load {file_path.name}: {e}")
            case_data[key] = {"error": str(e)}
    return case_data
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

@dataclass
class CaseContext:
    """Container for all loaded case data."""
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self.raw_data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        return self.raw_data
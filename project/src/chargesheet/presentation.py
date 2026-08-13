"""Deterministic, source-neutral formatting for charge-sheet presentation fields."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
import re
from typing import Any


_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME = re.compile(r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$")
_NARRATIVE_ATTRIBUTE_TOKENS = ("narrative", "statement_text", "complaint_text", "opinion_text", "summary", "description")
_LABELS = {"fir": "FIR", "fsl": "FSL", "id": "ID", "no": "No.", "number": "No.", "datetime": "Date and time"}


def label(value: str) -> str:
    """Convert a schema identifier into a readable, neutral label."""
    words = re.sub(r"([a-z])([A-Z])", r"\1 \2", value).replace("_", " ").split()
    rendered = [_LABELS.get(word.casefold(), word.casefold()) for word in words]
    if rendered:
        rendered[0] = rendered[0] if rendered[0].isupper() else rendered[0].capitalize()
    if len(rendered) >= 2 and rendered[-1] == "No.":
        return " ".join(rendered)
    return " ".join(rendered)


def _clean_text(value: str) -> str:
    return "\n".join(" ".join(line.split()) for line in value.splitlines() if line.strip())


def _format_date(value: str | date | datetime) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d %B %Y, %H:%M") if value.time() != datetime.min.time() else value.strftime("%d %B %Y")
    if isinstance(value, date):
        return value.strftime("%d %B %Y")
    if _DATE.fullmatch(value):
        return date.fromisoformat(value).strftime("%d %B %Y")
    if _DATETIME.fullmatch(value):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return _format_date(parsed)
    return value


def sentence(value: str) -> str:
    clean = _clean_text(value)
    if not clean:
        return ""
    return clean if clean.endswith((".", "!", "?", ";", ":")) else f"{clean}."


def format_value(value: Any, *, indent: int = 0) -> str:
    """Recursively render arbitrary JSON-like values without Python ``repr`` syntax.

    Collections retain their structure: mappings use labelled lines and sequences
    use bullet lines. ``None`` remains explicit when it is nested in a supplied
    structure, while missing charge-sheet fields are handled by the caller.
    """
    prefix = " " * indent
    if value is None:
        return "Not Available"
    if isinstance(value, datetime):
        return _format_date(value)
    if isinstance(value, date):
        return _format_date(value)
    if isinstance(value, Enum):
        return format_value(value.value, indent=indent)
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, float):
        return format(value, "g")
    if isinstance(value, str):
        return _clean_text(_format_date(value))
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            rendered = format_value(item, indent=indent + 2)
            if "\n" in rendered:
                lines.append(f"{prefix}{label(str(key))}:")
                lines.extend(f"{prefix}  {line}" for line in rendered.splitlines())
            else:
                lines.append(f"{prefix}{label(str(key))}: {rendered}")
        return "\n".join(lines) or f"{prefix}Not Available"
    if isinstance(value, (list, tuple, set, frozenset)):
        items = list(value)
        if isinstance(value, (set, frozenset)):
            items.sort(key=lambda item: str(item))
        lines: list[str] = []
        for item in items:
            rendered = format_value(item, indent=indent + 2)
            rendered_lines = rendered.splitlines() or ["Not Available"]
            if rendered_lines[0].lstrip().startswith("- "):
                lines.extend(f"{prefix}{line.lstrip()}" for line in rendered_lines)
            else:
                lines.append(f"{prefix}- {rendered_lines[0].lstrip()}")
                lines.extend(f"{prefix}  {line.lstrip()}" for line in rendered_lines[1:])
        return "\n".join(dict.fromkeys(lines)) or f"{prefix}Not Available"
    return _clean_text(str(value))


def format_inline(value: Any) -> str:
    """Use the same recursive formatter where an inline sentence is required."""
    return "; ".join(line.strip().lstrip("- ").strip() for line in format_value(value).splitlines() if line.strip())


def is_temporal_value(value: Any) -> bool:
    return isinstance(value, (date, datetime)) or (isinstance(value, str) and bool(_DATE.fullmatch(value) or _DATETIME.fullmatch(value)))


def unique_lines(values: list[str]) -> str:
    lines: list[str] = []
    for value in values:
        for line in value.splitlines():
            clean = line.strip()
            if clean and clean not in lines:
                lines.append(clean)
    return "\n".join(lines)


def is_narrative_attribute(name: str) -> bool:
    return any(token in name.casefold() for token in _NARRATIVE_ATTRIBUTE_TOKENS)


def document_action_statement(document_type: str, attributes: Mapping[str, Any]) -> str:
    """Describe a source-supported investigative activity without retelling events."""
    readable_type = label(document_type).lower()
    action = {
        "fir": "The FIR record was examined",
        "complaint": "The complaint record was examined",
        "witness statement": "A witness statement was recorded",
        "site plan": "The scene/site-plan record was documented",
        "spot panchnama": "The scene documentation record was examined",
        "seizure memo": "The seizure/recovery record was examined",
        "vehicle inspection": "The vehicle inspection record was examined",
        "medical report": "The medical record was examined",
        "postmortem report": "The post-mortem record was examined",
        "fsl report": "The forensic report was examined",
    }.get(readable_type, f"The {readable_type} record was examined")
    details = [
        f"{label(key)}: {format_inline(value)}"
        for key, value in attributes.items()
        if not is_narrative_attribute(key) and value is not None and format_inline(value) != "Not Available"
    ]
    return sentence(f"{action}: {'; '.join(details)}" if details else action)

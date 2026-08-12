"""Shared conversion of graph-backed values into audited canonical facts."""

from __future__ import annotations

from typing import Any

from .canonical_models import CanonicalFact


def project_fact(value: Any, provenance: tuple, source_path: str) -> CanonicalFact:
    confidences = [item.confidence for item in provenance if item.confidence is not None]
    return CanonicalFact(
        value=value,
        source_document_ids=tuple(dict.fromkeys(item.document_id for item in provenance)),
        references=provenance,
        source_path=source_path,
        confidence=sum(confidences) / len(confidences) if confidences else None,
        extraction_method=provenance[0].parser_name,
        timestamp=min(item.timestamp for item in provenance),
    )

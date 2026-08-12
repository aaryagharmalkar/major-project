"""Builds the finite evidence allow-list used to validate legal findings."""

from __future__ import annotations

from ..context.case_context import CaseContext
from .legal_findings import EvidenceMapping


class EvidenceMapper:
    def available(self, context: CaseContext) -> tuple[EvidenceMapping, ...]:
        mappings = []
        facts = context.medical_findings + context.forensic_findings + context.legal_section_references
        for fact in facts:
            mappings.append(EvidenceMapping(source_document_id=fact.source_document_ids[0], field_path=fact.source_path, description=str(fact.value), source_references=tuple(item.source_reference for item in fact.references)))
        for item in context.evidence + context.recovered_property:
            fact = item.description
            mappings.append(EvidenceMapping(source_document_id=fact.source_document_ids[0], field_path=fact.source_path, description=str(fact.value), source_references=tuple(entry.source_reference for entry in fact.references)))
        for event in context.relevant_timeline:
            fact = event.description
            mappings.append(EvidenceMapping(source_document_id=fact.source_document_ids[0], field_path=fact.source_path, description=str(fact.value), source_references=tuple(entry.source_reference for entry in fact.references)))
        return tuple(mappings)

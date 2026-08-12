"""Constrained legal reasoning using supplied references and evidence mappings only."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any

from pydantic import ValidationError

from ..context.case_context import CaseContext
from ..validation.validation_models import ValidationDisposition
from .evidence_mapper import EvidenceMapper
from .legal_findings import EvidenceStrength, LegalFinding, LegalFindingStatus, LegalFindings
from .legal_rules import LegalReferenceProvider


class LegalReasoningClient(ABC):
    @abstractmethod
    def generate_json(self, prompt: str) -> dict[str, Any]: ...


class LegalReasoner:
    def __init__(self, reference_provider: LegalReferenceProvider, client: LegalReasoningClient | None = None, *, max_attempts: int = 2) -> None:
        self.reference_provider, self.client, self.max_attempts = reference_provider, client, max_attempts
        self.evidence_mapper = EvidenceMapper()

    def reason(self, context: CaseContext) -> LegalFindings:
        available = self.evidence_mapper.available(context)
        references = self.reference_provider.references_for(context)
        if context.validation_disposition == ValidationDisposition.FINAL_BLOCKED.value:
            return LegalFindings(findings=(), review_required=True, validation_disposition=context.validation_disposition, retry_count=0)
        if self.client is not None:
            return self._reason_with_client(context, references, available)
        findings = tuple(self._deterministic_finding(reference, available, context) for reference in references)
        return LegalFindings(findings=findings, review_required=context.validation_disposition != ValidationDisposition.DRAFT_ALLOWED.value or any(item.review_required for item in findings) or not references, validation_disposition=context.validation_disposition, retry_count=0)

    def _deterministic_finding(self, reference, evidence, context):
        conflicts = bool(context.conflicts)
        elements_supported = not reference.required_elements or all(any(element.casefold() in mapping.description.casefold() for mapping in evidence) for element in reference.required_elements)
        status = LegalFindingStatus.CONFLICTED if conflicts else LegalFindingStatus.SUPPORTED if evidence and elements_supported else LegalFindingStatus.INSUFFICIENT_EVIDENCE
        strength = EvidenceStrength.HIGH if len(evidence) >= 2 else EvidenceStrength.MEDIUM if evidence else EvidenceStrength.LOW
        selected = evidence or self._context_evidence(context)
        return LegalFinding(legal_reference_id=reference.section_id, offence=reference.offence_name, proposed_section=reference.section_number, description=reference.description, supporting_evidence=selected, contradicting_evidence=(), evidence_strength=strength, confidence=0.8 if evidence else 0.2, status=status, review_required=status != LegalFindingStatus.SUPPORTED, source_references=tuple(item for mapping in selected for item in mapping.source_references))

    def _reason_with_client(self, context, references, available) -> LegalFindings:
        allowed = {(item.source_document_id, item.field_path) for item in available}
        prompt = json.dumps({"context": context.model_dump(mode="json"), "legal_references": [item.model_dump(mode="json") for item in references], "allowed_evidence": [item.model_dump(mode="json") for item in available], "schema": LegalFindings.model_json_schema()}, default=str)
        errors = []
        for attempt in range(self.max_attempts):
            try:
                result = LegalFindings.model_validate(self.client.generate_json(prompt))
                if result.validation_disposition != context.validation_disposition: raise ValueError("Validation disposition cannot be changed by legal reasoning")
                legal_sections = {(item.section_id, item.section_number) for item in references}
                if any((item.legal_reference_id, item.proposed_section) not in legal_sections or any((e.source_document_id, e.field_path) not in allowed for e in item.supporting_evidence) for item in result.findings): raise ValueError("Finding uses an unavailable legal section or evidence mapping")
                return result.model_copy(update={"retry_count": attempt, "review_required": result.review_required or context.validation_disposition != ValidationDisposition.DRAFT_ALLOWED.value})
            except (ValidationError, ValueError, KeyError) as exc: errors.append(str(exc))
        return LegalFindings(findings=(), review_required=True, validation_disposition=context.validation_disposition, retry_count=self.max_attempts)

    @staticmethod
    def _context_evidence(context: CaseContext):
        # LegalFinding always needs real evidence; context may still have no eligible evidence.
        mapper = EvidenceMapper().available(context)
        if not mapper: raise ValueError("Legal references cannot yield a finding without evidence mappings")
        return mapper

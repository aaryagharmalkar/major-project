"""Second-line validation for data assembled before rendering."""

from __future__ import annotations

from ..domain.common import DomainModel
from .form_if5_schema import ChargeSheetData, ChargeSheetField, FieldStatus


class ChargeSheetValidationReport(DomainModel):
    errors: tuple[str, ...] = ()
    review_required: bool = False


class ChargeSheetValidator:
    def validate(self, data: ChargeSheetData) -> ChargeSheetValidationReport:
        fields = [data.case_number, data.police_station, data.court, data.case_summary, data.detailed_facts, data.investigation_conducted, data.evidence_analysis, data.final_opinion, data.signature, *data.medical_findings, *data.forensic_findings, *data.vehicle_findings, *data.legal_sections]
        for rows in (data.complainants, data.victims, data.accused, data.witnesses, data.timeline, data.documentary_evidence, data.material_evidence, data.annexures):
            fields.extend(field for row in rows for field in (row.description, row.exhibit))
        for finding in data.legal_findings:
            fields.extend((finding.offence, finding.proposed_section, finding.description, *finding.supporting_evidence, *finding.contradicting_evidence))
        errors = []
        for field in fields:
            if field.status in {FieldStatus.POPULATED, FieldStatus.REVIEW_REQUIRED} and (not field.value or not field.source_references):
                errors.append("Rendered field lacks a value or source reference.")
            if field.status == FieldStatus.UNAVAILABLE and field.value:
                errors.append("Unavailable field contains an unsupported value.")
        return ChargeSheetValidationReport(errors=tuple(errors), review_required=any(field.review_required for field in fields))

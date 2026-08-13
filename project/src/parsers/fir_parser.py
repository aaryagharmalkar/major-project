from ..domain.documents import DocumentType
from ..domain.parsed_documents import FIR
from .base_parser import BaseDocumentParser


class FIRParser(BaseDocumentParser[FIR]):
    document_type = DocumentType.FIR
    model_type = FIR
    supported_entity_fields = ("complainant_name", "accused_names", "victim_names", "vehicle_registrations")

    def _document_specific_instructions(self) -> str:
        return (
            "For this FIR, preserve each explicitly identified complainant, accused or person named in the "
            "complaint, victim, and vehicle registration in its corresponding field. Do not assign a role from "
            "narrative implication; leave the field unavailable when the document does not explicitly identify it."
        )

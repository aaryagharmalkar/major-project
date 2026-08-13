from ..domain.documents import DocumentType
from ..domain.parsed_documents import Complaint
from .base_parser import BaseDocumentParser


class ComplaintParser(BaseDocumentParser[Complaint]):
    document_type = DocumentType.COMPLAINT
    model_type = Complaint
    supported_entity_fields = ("complainant_name", "person_complained_against_names", "victim_names", "vehicle_registrations")

    def _document_specific_instructions(self) -> str:
        return (
            "For this complaint, preserve each explicitly identified complainant, person complained against, "
            "victim, and vehicle registration in its corresponding field. Do not infer an accused, victim, or "
            "vehicle from an unlabelled narrative mention; leave the field unavailable when absent."
        )

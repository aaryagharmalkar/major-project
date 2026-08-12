from ..domain.documents import DocumentType
from ..domain.parsed_documents import MedicalReport
from .base_parser import BaseDocumentParser


class MedicalReportParser(BaseDocumentParser[MedicalReport]):
    document_type = DocumentType.MEDICAL_REPORT
    model_type = MedicalReport

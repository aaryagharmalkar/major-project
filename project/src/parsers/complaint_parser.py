from ..domain.documents import DocumentType
from ..domain.parsed_documents import Complaint
from .base_parser import BaseDocumentParser


class ComplaintParser(BaseDocumentParser[Complaint]):
    document_type = DocumentType.COMPLAINT
    model_type = Complaint

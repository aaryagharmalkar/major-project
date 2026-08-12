from ..domain.documents import DocumentType
from ..domain.parsed_documents import FIR
from .base_parser import BaseDocumentParser


class FIRParser(BaseDocumentParser[FIR]):
    document_type = DocumentType.FIR
    model_type = FIR

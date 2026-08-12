from ..domain.documents import DocumentType
from ..domain.parsed_documents import CaseDiary
from .base_parser import BaseDocumentParser


class CaseDiaryParser(BaseDocumentParser[CaseDiary]):
    document_type = DocumentType.CASE_DIARY
    model_type = CaseDiary

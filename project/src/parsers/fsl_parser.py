from ..domain.documents import DocumentType
from ..domain.parsed_documents import FSLReport
from .base_parser import BaseDocumentParser


class FSLParser(BaseDocumentParser[FSLReport]):
    document_type = DocumentType.FSL_REPORT
    model_type = FSLReport

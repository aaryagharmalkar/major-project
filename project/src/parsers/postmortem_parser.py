from ..domain.documents import DocumentType
from ..domain.parsed_documents import PostmortemReport
from .base_parser import BaseDocumentParser


class PostmortemParser(BaseDocumentParser[PostmortemReport]):
    document_type = DocumentType.POSTMORTEM_REPORT
    model_type = PostmortemReport

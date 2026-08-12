from ..domain.documents import DocumentType
from ..domain.parsed_documents import ArrestMemo
from .base_parser import BaseDocumentParser


class ArrestMemoParser(BaseDocumentParser[ArrestMemo]):
    document_type = DocumentType.ARREST_MEMO
    model_type = ArrestMemo

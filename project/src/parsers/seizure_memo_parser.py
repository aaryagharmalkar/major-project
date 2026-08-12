from ..domain.documents import DocumentType
from ..domain.parsed_documents import SeizureMemo
from .base_parser import BaseDocumentParser


class SeizureMemoParser(BaseDocumentParser[SeizureMemo]):
    document_type = DocumentType.SEIZURE_MEMO
    model_type = SeizureMemo

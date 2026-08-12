from ..domain.documents import DocumentType
from ..domain.parsed_documents import WitnessStatement
from .base_parser import BaseDocumentParser


class WitnessParser(BaseDocumentParser[WitnessStatement]):
    document_type = DocumentType.WITNESS_STATEMENT
    model_type = WitnessStatement

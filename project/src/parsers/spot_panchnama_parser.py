from ..domain.documents import DocumentType
from ..domain.parsed_documents import SpotPanchnama
from .base_parser import BaseDocumentParser


class SpotPanchnamaParser(BaseDocumentParser[SpotPanchnama]):
    document_type = DocumentType.SPOT_PANCHNAMA
    model_type = SpotPanchnama

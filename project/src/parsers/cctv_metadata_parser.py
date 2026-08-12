from ..domain.documents import DocumentType
from ..domain.parsed_documents import CCTVMetadata
from .base_parser import BaseDocumentParser


class CCTVMetadataParser(BaseDocumentParser[CCTVMetadata]):
    document_type = DocumentType.CCTV_IMAGE
    model_type = CCTVMetadata

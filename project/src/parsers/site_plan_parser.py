from ..domain.documents import DocumentType
from ..domain.parsed_documents import SitePlan
from .base_parser import BaseDocumentParser


class SitePlanParser(BaseDocumentParser[SitePlan]):
    document_type = DocumentType.SITE_PLAN
    model_type = SitePlan

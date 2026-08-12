from ..domain.documents import DocumentType
from ..domain.parsed_documents import VehicleInspection
from .base_parser import BaseDocumentParser


class VehicleInspectionParser(BaseDocumentParser[VehicleInspection]):
    document_type = DocumentType.VEHICLE_INSPECTION
    model_type = VehicleInspection

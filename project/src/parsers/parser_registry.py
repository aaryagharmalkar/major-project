"""Registry for mapping declared document types to independent parser instances."""

from __future__ import annotations

from ..domain.documents import DocumentType
from .base_parser import BaseDocumentParser, UnknownDocumentParser


def create_default_parser_registry(client) -> "ParserRegistry":
    """Compose every independent parser without coupling workflow code to types."""
    from .arrest_memo_parser import ArrestMemoParser
    from .case_diary_parser import CaseDiaryParser
    from .cctv_metadata_parser import CCTVMetadataParser
    from .complaint_parser import ComplaintParser
    from .fir_parser import FIRParser
    from .fsl_parser import FSLParser
    from .medical_report_parser import MedicalReportParser
    from .postmortem_parser import PostmortemParser
    from .seizure_memo_parser import SeizureMemoParser
    from .site_plan_parser import SitePlanParser
    from .spot_panchnama_parser import SpotPanchnamaParser
    from .vehicle_inspection_parser import VehicleInspectionParser
    from .witness_parser import WitnessParser

    registry = ParserRegistry(UnknownDocumentParser(client))
    for parser_type in (
        FIRParser,
        ComplaintParser,
        MedicalReportParser,
        PostmortemParser,
        FSLParser,
        WitnessParser,
        CaseDiaryParser,
        ArrestMemoParser,
        SeizureMemoParser,
        SpotPanchnamaParser,
        VehicleInspectionParser,
        SitePlanParser,
        CCTVMetadataParser,
    ):
        registry.register(parser_type(client))
    return registry


class ParserRegistry:
    def __init__(self, unknown_parser: UnknownDocumentParser) -> None:
        self._parsers: dict[DocumentType, BaseDocumentParser] = {}
        self._unknown_parser = unknown_parser

    def register(self, parser: BaseDocumentParser) -> BaseDocumentParser:
        if parser.document_type in self._parsers:
            raise ValueError(f"A parser is already registered for {parser.document_type}")
        self._parsers[parser.document_type] = parser
        return parser

    def get(self, document_type: DocumentType) -> BaseDocumentParser:
        return self._parsers.get(document_type, self._unknown_parser)

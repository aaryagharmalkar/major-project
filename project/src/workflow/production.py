"""Production composition root for the typed investigation workflow."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from ..chargesheet.chargesheet_stage import ChargeSheetStage
from ..context.context_stage import CaseContextStage
from ..extraction.gemini_ocr import GeminiOCRClient
from ..extraction.ocr_client import OCRClient
from ..extraction.ocr_stage import OCRStage
from ..intake.document_intake_stage import DocumentIntakeStage
from ..intake.file_validator import FileValidator
from ..intake.upload_manager import IncomingUpload, UploadManager
from ..config import Config
from ..knowledge_graph.graph_stage import GraphStage
from ..legal.legal_reasoner import LegalReasoner
from ..legal.legal_rules import LegalReferenceProvider, LocalLegalReferenceProvider
from ..legal.legal_stage import LegalReasoningStage
from ..normalization.canonical_stage import CanonicalInvestigationStage
from ..parsers.base_parser import GeminiParserClient, ParserClient
from ..parsers.parser_registry import ParserRegistry, create_default_parser_registry
from ..parsers.parser_stage import ParserStage
from ..validation.evidence_validator import EvidenceValidator
from ..validation.validation_stage import EvidenceValidationStage
from .context import ContextItem, WorkflowContext
from .engine import WorkflowEngine
from .registry import StageRegistry
from .state import WorkflowState


STAGE_ORDER = (
    "document_intake",
    "ocr",
    "document_parsing",
    "investigation_knowledge_graph",
    "canonical_investigation",
    "evidence_validation",
    "case_context",
    "legal_reasoning",
    "chargesheet_population",
)


def create_workflow_context(case_id: UUID, uploads: tuple[IncomingUpload, ...]) -> WorkflowContext:
    """Create the sole workflow input snapshot from transport-neutral uploads."""
    return WorkflowContext(
        case_id=case_id,
        pending_uploads=tuple(ContextItem(key=f"upload:{index}", value=upload) for index, upload in enumerate(uploads, 1)),
        execution_state=WorkflowState(case_id=case_id),
    )


def create_production_registry(
    storage_root: Path,
    *,
    gemini_api_key: str | None = None,
    gemini_model: str | None = None,
    ocr_client: OCRClient | None = None,
    parser_client: ParserClient | None = None,
    parser_registry: ParserRegistry | None = None,
    legal_reference_provider: LegalReferenceProvider | None = None,
    legal_reference_path: Path | None = None,
    legal_reference_version: str | None = None,
    legal_reasoner: LegalReasoner | None = None,
    evidence_validator: EvidenceValidator | None = None,
) -> StageRegistry:
    """Compose the approved Phase 1-10 stages in their required execution order."""
    resolved_provider = legal_reference_provider or LocalLegalReferenceProvider.load(legal_reference_path, legal_reference_version)
    resolved_ocr_client = ocr_client or GeminiOCRClient(api_key=gemini_api_key or Config.GEMINI_API_KEY, model=gemini_model or Config.GEMINI_MODEL)
    resolved_parser_client = parser_client or GeminiParserClient(api_key=gemini_api_key or Config.GEMINI_API_KEY, model=gemini_model or Config.GEMINI_MODEL)
    resolved_parser_registry = parser_registry or create_default_parser_registry(resolved_parser_client)
    resolved_reasoner = legal_reasoner or LegalReasoner(resolved_provider)
    registry = StageRegistry((
        DocumentIntakeStage(storage_root, UploadManager(storage_root, validator=FileValidator(Config.MAX_UPLOAD_FILE_SIZE_BYTES), max_case_size_bytes=Config.MAX_CASE_UPLOAD_SIZE_BYTES)),
        OCRStage(storage_root, resolved_ocr_client),
        ParserStage(storage_root, resolved_parser_registry),
        GraphStage(storage_root),
        CanonicalInvestigationStage(storage_root),
        EvidenceValidationStage(storage_root, validator=evidence_validator),
        CaseContextStage(storage_root),
        LegalReasoningStage(storage_root, reasoner=resolved_reasoner),
        ChargeSheetStage(storage_root),
    ))
    if tuple(stage.name for stage in registry.stages) != STAGE_ORDER:
        raise RuntimeError("Production workflow stage order is invalid")
    return registry


def run_production_workflow(
    storage_root: Path,
    context: WorkflowContext,
    **dependencies: object,
):
    """Run a fully composed typed workflow; no legacy code participates."""
    registry = create_production_registry(storage_root, **dependencies)
    return WorkflowEngine(registry).run(context)

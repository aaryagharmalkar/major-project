"""Orchestrate deterministic document generation for a validated MasterCase."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Sequence

from pydantic import BaseModel, Field

from generator.document_generators.base_generator import BaseDocumentGenerator
from generator.pdf.pdf_pipeline import PDFPipeline
from generator.schemas.master_case_schema import MasterCase

logger = logging.getLogger(__name__)


class GenerationReportItem(BaseModel):
    """Outcome for a single document generator run."""

    name: str
    status: str
    output_files: list[str] = Field(default_factory=list)
    error: str | None = None


class GenerationReport(BaseModel):
    """Summary of the orchestration run."""

    case_id: str
    output_directory: str
    success: bool
    generated_files: list[str] = Field(default_factory=list)
    items: list[GenerationReportItem] = Field(default_factory=list)


class CaseBuilder:
    """Create a case output directory and run registered document generators."""

    def __init__(
        self,
        master_case: MasterCase,
        output_root: str | Path,
        generators: Sequence[BaseDocumentGenerator[Any]] | None = None,
        *,
        logger_instance: logging.Logger | None = None,
    ) -> None:
        self._master_case = master_case
        self._output_root = Path(output_root).expanduser().resolve()
        self._generators = list(generators or [])
        self._logger = logger_instance or logger
        self._pdf_pipeline = PDFPipeline(self._output_root)

    def register_generator(self, generator: BaseDocumentGenerator[Any]) -> None:
        """Register a document generator for execution."""

        self._generators.append(generator)

    def register_default_generators(self) -> None:
        """Register the built-in investigation document generators in generation order."""

        from generator.document_generators.arrest_generator import ArrestDocumentGenerator
        from generator.document_generators.chargesheet_generator import ChargeSheetDocumentGenerator
        from generator.document_generators.complaint_generator import ComplaintDocumentGenerator
        from generator.document_generators.diary_generator import DiaryDocumentGenerator
        from generator.document_generators.fir_generator import FIRDocumentGenerator
        from generator.document_generators.fsl_generator import FSLDocumentGenerator
        from generator.document_generators.medical_generator import MedicalDocumentGenerator
        from generator.document_generators.seizure_generator import SeizureDocumentGenerator
        from generator.document_generators.spot_panchanama_generator import SpotPanchanamaDocumentGenerator
        from generator.document_generators.witness_generator import WitnessDocumentGenerator

        self.register_generator(FIRDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(ComplaintDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(WitnessDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(MedicalDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(SeizureDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(SpotPanchanamaDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(ArrestDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(FSLDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(DiaryDocumentGenerator(self._master_case, self._output_root))
        self.register_generator(ChargeSheetDocumentGenerator(self._master_case, self._output_root))

    def build_case_directory(self) -> Path:
        """Create the case output directory and required subfolders."""

        case_id = self._master_case.case_information.case_id
        normalized_case_id = case_id if case_id.startswith("CASE_") else f"CASE_{case_id}"
        case_directory = self._output_root / normalized_case_id
        case_directory.mkdir(parents=True, exist_ok=True)

        for subfolder in ("documents", "pdfs", "ocr", "embeddings", "ground_truth"):
            (case_directory / subfolder).mkdir(parents=True, exist_ok=True)

        return case_directory

    def run(self) -> GenerationReport:
        """Run all registered generators and continue on failures."""

        case_directory = self.build_case_directory()
        self._logger.info("Starting generation for case '%s' in '%s'", self._master_case.case_information.case_id, case_directory)

        report_items: list[GenerationReportItem] = []
        generated_files: list[str] = []

        for generator in self._generators:
            generator_name = type(generator).__name__
            generator_output_dir = case_directory / "documents"
            generator._output_directory = generator_output_dir
            generator._output_directory.mkdir(parents=True, exist_ok=True)

            try:
                self._logger.info("Running generator '%s'", generator_name)
                output_paths = generator.generate()
                relative_paths = [str(path.relative_to(case_directory)) for path in output_paths]
                generated_files.extend(relative_paths)

                for output_path in output_paths:
                    if output_path.suffix.lower() != ".md":
                        continue
                    document_type = self._infer_document_type(output_path.name)
                    self._pdf_pipeline._output_directory = case_directory / "pdfs"
                    self._pdf_pipeline._output_directory.mkdir(parents=True, exist_ok=True)
                    pdf_path = self._pdf_pipeline.render_markdown(
                        document_type,
                        output_path.read_text(encoding="utf-8"),
                        title=output_path.stem.replace("_", " ").title(),
                        output_name=output_path.stem + ".pdf",
                    )
                    generated_files.append(str(pdf_path.relative_to(case_directory)))

                report_items.append(
                    GenerationReportItem(
                        name=generator_name,
                        status="success",
                        output_files=relative_paths,
                    )
                )
            except Exception as exc:  # pragma: no cover - defensive orchestration path
                self._logger.exception("Generator '%s' failed", generator_name)
                report_items.append(
                    GenerationReportItem(
                        name=generator_name,
                        status="failed",
                        error=str(exc),
                    )
                )

        report = GenerationReport(
            case_id=self._master_case.case_information.case_id,
            output_directory=str(case_directory),
            success=all(item.status == "success" for item in report_items),
            generated_files=generated_files,
            items=report_items,
        )
        return report

    @staticmethod
    def _infer_document_type(filename: str) -> str:
        lower_name = filename.lower()
        if lower_name.startswith("fir"):
            return "FIR"
        if lower_name.startswith("complaint"):
            return "Complaint"
        if lower_name.startswith("witness"):
            return "Witness Statement"
        if lower_name.startswith("medical"):
            return "Medical Report"
        if lower_name.startswith("seizure"):
            return "Seizure Memo"
        if lower_name.startswith("spot"):
            return "Spot Panchanama"
        if lower_name.startswith("arrest"):
            return "Arrest Memo"
        if lower_name.startswith("fsl"):
            return "FSL Report"
        if lower_name.startswith("case"):
            return "Case Diary"
        if lower_name.startswith("charge"):
            return "Charge Sheet"
        return "Document"

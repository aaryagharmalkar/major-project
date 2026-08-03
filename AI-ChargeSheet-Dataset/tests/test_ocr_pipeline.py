from __future__ import annotations

import json
from pathlib import Path

from generator.ocr.gemini_ocr import GeminiOCRClient
from generator.ocr.ocr_evaluator import OCREvaluator
from generator.ocr.ocr_pipeline import OCRPipeline
from generator.ocr.ocr_result import OCRExtractionResult


class DummyOCRClient(GeminiOCRClient):
    def extract(self, pdf_path: Path) -> OCRExtractionResult:
        return OCRExtractionResult(document_type=pdf_path.stem, extracted_data={"title": pdf_path.stem})


def test_ocr_pipeline_and_evaluator(tmp_path: Path) -> None:
    case_directory = tmp_path / "CASE_001"
    (case_directory / "pdfs").mkdir(parents=True, exist_ok=True)
    (case_directory / "ground_truth").mkdir(parents=True, exist_ok=True)
    (case_directory / "ocr").mkdir(parents=True, exist_ok=True)

    pdf_path = case_directory / "pdfs" / "fir.pdf"
    pdf_path.write_bytes(b"fake pdf")

    ground_truth_payload = {"document_type": "FIR", "extracted_data": {"title": "fir"}}
    (case_directory / "ground_truth" / "fir.json").write_text(json.dumps(ground_truth_payload), encoding="utf-8")

    pipeline = OCRPipeline(DummyOCRClient())
    outputs = pipeline.run(case_directory)

    assert len(outputs) == 1
    assert outputs[0].exists()

    evaluator = OCREvaluator()
    evaluations = evaluator.evaluate(case_directory)

    assert len(evaluations) == 1
    assert evaluations[0].metrics.document_accuracy == 1.0

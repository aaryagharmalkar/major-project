"""Evaluate OCR extraction quality against case ground truth data."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from generator.ocr.ocr_result import OCREvaluationMetrics, OCREvaluationResult

logger = logging.getLogger(__name__)


class OCREvaluator:
    """Compare OCR outputs with local ground-truth JSON to compute quality metrics."""

    def __init__(self, *, strict: bool = False) -> None:
        self._strict = strict

    def evaluate(self, case_directory: str | Path) -> list[OCREvaluationResult]:
        case_path = Path(case_directory).expanduser().resolve()
        ocr_directory = case_path / "ocr"
        ground_truth_directory = case_path / "ground_truth"
        evaluations: list[OCREvaluationResult] = []

        if not ocr_directory.exists() or not ground_truth_directory.exists():
            return evaluations

        for extracted_path in sorted(ocr_directory.glob("*.json")):
            ground_truth_path = ground_truth_directory / extracted_path.name
            if not ground_truth_path.exists():
                continue

            extracted_payload = json.loads(extracted_path.read_text(encoding="utf-8"))
            ground_truth_payload = json.loads(ground_truth_path.read_text(encoding="utf-8"))
            metrics = self._compute_metrics(extracted_payload, ground_truth_payload)
            result = OCREvaluationResult(
                document_type=extracted_payload.get("document_type", extracted_path.stem),
                source_pdf=f"{extracted_path.stem}.pdf",
                extracted_json=extracted_path.name,
                metrics=metrics,
            )
            evaluations.append(result)

        evaluation_path = case_path / "evaluation.json"
        evaluation_path.write_text(json.dumps([item.model_dump() for item in evaluations], indent=2), encoding="utf-8")
        return evaluations

    def _compute_metrics(self, extracted_payload: dict[str, Any], ground_truth_payload: dict[str, Any]) -> OCREvaluationMetrics:
        extracted_fields = set(str(key) for key in extracted_payload.get("extracted_data", {}).keys())
        ground_truth_fields = set(str(key) for key in ground_truth_payload.get("extracted_data", {}).keys())

        if not ground_truth_fields:
            document_accuracy = 1.0 if not extracted_fields else 0.0
            return OCREvaluationMetrics(document_accuracy=document_accuracy)

        true_positives = len(extracted_fields & ground_truth_fields)
        false_positives = len(extracted_fields - ground_truth_fields)
        false_negatives = len(ground_truth_fields - extracted_fields)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

        document_accuracy = 1.0 if not false_positives and not false_negatives else 0.0
        return OCREvaluationMetrics(
            entity_accuracy=round(true_positives / len(ground_truth_fields), 4) if ground_truth_fields else 0.0,
            missing_fields=false_negatives,
            incorrect_fields=false_positives,
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            document_accuracy=round(document_accuracy, 4),
        )

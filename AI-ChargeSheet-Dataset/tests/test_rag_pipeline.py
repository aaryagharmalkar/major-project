import json
from pathlib import Path

from generator.rag.chunker import Chunker
from generator.rag.metadata_builder import MetadataBuilder
from generator.rag.qdrant_indexer import QdrantIndexer
from generator.rag.rag_pipeline import RAGPipeline


def test_rag_pipeline_writes_expected_artifacts(tmp_path: Path) -> None:
    case_dir = tmp_path / "CASE_999"
    case_dir.mkdir()
    ocr_path = case_dir / "ocr.json"
    ocr_path.write_text(
        json.dumps(
            {
                "document_type": "FIR",
                "extracted_data": {
                    "narrative": "A suspicious person was observed near the police station.",
                    "evidence": "A bag was recovered.",
                },
            }
        ),
        encoding="utf-8",
    )

    pipeline = RAGPipeline(
        chunker=Chunker(chunk_size=100),
        metadata_builder=MetadataBuilder(),
        indexer=QdrantIndexer(output_directory=tmp_path / "rag_output"),
    )
    result = pipeline.run(case_dir, ocr_path, output_directory=case_dir / "rag")

    assert result["chunk_count"] >= 1
    assert result["embedding_count"] >= 1

    chunks_path = case_dir / "rag" / "chunks.json"
    metadata_path = case_dir / "rag" / "metadata.json"
    embeddings_path = case_dir / "rag" / "embeddings.json"
    report_path = case_dir / "rag" / "index_report.json"

    assert chunks_path.exists()
    assert metadata_path.exists()
    assert embeddings_path.exists()
    assert report_path.exists()

    payload = json.loads(chunks_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    embeddings = json.loads(embeddings_path.read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))

    assert len(payload) == len(metadata)
    assert len(embeddings) == len(payload)
    assert report["record_count"] == len(payload)

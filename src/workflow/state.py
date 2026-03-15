"""LangGraph 工作流状态定义"""
from typing import TypedDict

from src.document.metadata_extractor import ParagraphChunk
from src.analysis.scorer import SimilarPair


class TenderComparisonState(TypedDict):
    task_id: str
    doc_ids: list[str]
    file_paths: dict[str, str]
    doc_names: dict[str, str]
    comparison_mode: str
    raw_texts: dict[str, str]
    chunks: dict[str, list[ParagraphChunk]]
    embeddings_stored: bool
    candidate_pairs: list[SimilarPair]
    scored_pairs: list[SimilarPair]
    llm_analyzed_pairs: list[SimilarPair]
    current_node: str
    error_message: str | None
    processing_progress: float
    report: dict | None
    overall_risk_level: str
    overall_similarity_rate: float
    structure_similarity: dict | None
    field_overlaps: list[dict]

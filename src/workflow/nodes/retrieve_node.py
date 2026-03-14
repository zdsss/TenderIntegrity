"""retrieve_similar_pairs 节点"""
import logging
from config.settings import settings
from src.analysis.similarity import SimilarityEngine
from src.vectorstore.embedding_service import EmbeddingService
from src.vectorstore.repository import ChromaRepository
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def retrieve_similar_pairs(state: TenderComparisonState) -> dict:
    embedding_service = EmbeddingService(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        batch_size=settings.embedding_batch_size,
        use_api=settings.embedding_use_api,
        api_key=settings.dashscope_api_key or None,
        api_base_url=settings.dashscope_base_url or None,
    )
    repo = ChromaRepository(embedding_service, persist_dir=settings.chroma_persist_dir)
    engine = SimilarityEngine(
        chroma_repo=repo,
        top_k=settings.top_k_similar,
        min_similarity=settings.vector_similarity_threshold,
    )
    candidate_pairs = engine.find_similar_pairs(
        chunks_by_doc=state["chunks"],
        task_id=state["task_id"],
        mode=state.get("comparison_mode", "pairwise"),
    )
    logger.info(f"检索到 {len(candidate_pairs)} 个候选相似对")
    return {"candidate_pairs": candidate_pairs, "current_node": "retrieve_similar_pairs", "processing_progress": 0.65}

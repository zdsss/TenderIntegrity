"""embed_and_store 节点"""
import logging
from config.settings import settings
from src.vectorstore.embedding_service import EmbeddingService
from src.vectorstore.repository import ChromaRepository
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def embed_and_store(state: TenderComparisonState) -> dict:
    embedding_service = EmbeddingService(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        batch_size=settings.embedding_batch_size,
        use_api=settings.embedding_use_api,
        api_key=settings.dashscope_api_key or None,
        api_base_url=settings.dashscope_base_url or None,
    )
    repo = ChromaRepository(embedding_service, persist_dir=settings.chroma_persist_dir)
    for doc_id, chunk_list in state["chunks"].items():
        repo.upsert_chunks(chunk_list, state["task_id"])
        logger.info(f"文档 {doc_id}: {len(chunk_list)} 个段落块写入 ChromaDB")
    return {"embeddings_stored": True, "current_node": "embed_and_store", "processing_progress": 0.5}

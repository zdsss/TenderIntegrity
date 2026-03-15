"""filter_whitelist 节点"""
import logging
from config.settings import settings
from src.analysis.whitelist_filter import WhitelistFilter
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def _build_whitelist_filter() -> WhitelistFilter:
    """构建带向量白名单的过滤器（懒加载 embedding 模型）"""
    chroma_repo = None
    try:
        from src.vectorstore.embedding_service import EmbeddingService
        from src.vectorstore.repository import ChromaRepository

        embedding_service = EmbeddingService(
            model_name=settings.embedding_model,
            device=settings.embedding_device,
            batch_size=settings.embedding_batch_size,
            use_api=settings.embedding_use_api,
            api_key=settings.dashscope_api_key or None,
            api_base_url=settings.dashscope_base_url or None,
        )
        repo = ChromaRepository(
            embedding_service, persist_dir=settings.chroma_persist_dir
        )
        # 仅当白名单向量集合有内容时才启用
        collection = repo._get_collection("whitelist_phrases")
        if collection.count() > 0:
            chroma_repo = repo
            logger.info("白名单向量层已激活（第2层）")
        else:
            logger.info("白名单向量集合为空，跳过第2层向量过滤")
    except Exception as e:
        logger.warning(f"白名单向量层初始化失败，仅使用正则层: {e}")

    return WhitelistFilter(
        whitelist_dir=settings.whitelist_dir,
        chroma_repo=chroma_repo,
        whitelist_threshold=settings.whitelist_similarity_threshold,
    )


def filter_whitelist(state: TenderComparisonState) -> dict:
    whitelist_filter = _build_whitelist_filter()
    updated_chunks = {}
    for doc_id, chunk_list in state["chunks"].items():
        filtered = whitelist_filter.filter_chunks(chunk_list)
        updated_chunks[doc_id] = filtered
        wl_count = sum(1 for c in filtered if c.is_whitelisted)
        logger.info(f"文档 {doc_id}: {wl_count}/{len(filtered)} 个段落标记为白名单")
    return {
        "chunks": updated_chunks,
        "current_node": "filter_whitelist",
        "processing_progress": 0.3,
    }

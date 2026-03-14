"""filter_whitelist 节点"""
import logging
from config.settings import settings
from src.analysis.whitelist_filter import WhitelistFilter
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def filter_whitelist(state: TenderComparisonState) -> dict:
    whitelist_filter = WhitelistFilter(whitelist_dir=settings.whitelist_dir)
    updated_chunks = {}
    for doc_id, chunk_list in state["chunks"].items():
        filtered = whitelist_filter.filter_chunks(chunk_list)
        updated_chunks[doc_id] = filtered
        wl_count = sum(1 for c in filtered if c.is_whitelisted)
        logger.info(f"文档 {doc_id}: {wl_count}/{len(filtered)} 个段落标记为白名单")
    return {"chunks": updated_chunks, "current_node": "filter_whitelist", "processing_progress": 0.3}

"""chunk_documents 节点"""
import logging
from src.document.parser import DocumentParser
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def chunk_documents(state: TenderComparisonState) -> dict:
    parser = DocumentParser()
    chunks: dict = {}
    for doc_id, file_path in state["file_paths"].items():
        try:
            doc_chunks = parser.parse_to_chunks(file_path, doc_id)
            chunks[doc_id] = doc_chunks
            logger.info(f"文档 {doc_id} 切分完成，{len(doc_chunks)} 个段落块")
        except Exception as e:
            raise RuntimeError(f"切分文档 {doc_id} 失败: {e}") from e
    return {"chunks": chunks, "current_node": "chunk_documents", "processing_progress": 0.2}

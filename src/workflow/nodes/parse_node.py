"""parse_documents 节点"""
import logging
from src.document.parser import DocumentParser
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def parse_documents(state: TenderComparisonState) -> dict:
    parser = DocumentParser()
    raw_texts: dict[str, str] = {}
    for doc_id, file_path in state["file_paths"].items():
        try:
            text = parser.parse_to_text(file_path)
            raw_texts[doc_id] = text
            logger.info(f"文档 {doc_id} 解析完成，{len(text)} 字符")
        except Exception as e:
            raise RuntimeError(f"解析文档 {doc_id} ({file_path}) 失败: {e}") from e
    return {"raw_texts": raw_texts, "current_node": "parse_documents", "processing_progress": 0.1}

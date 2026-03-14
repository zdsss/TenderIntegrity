"""DocumentParser 统一接口（工厂模式）"""
import logging
from pathlib import Path

from src.document.metadata_extractor import ParagraphChunk
from src.document.chunker import ChunkSplitter

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".text"}


class DocumentParser:
    """统一文档解析入口，根据文件扩展名分发到对应解析器"""

    def __init__(self, chunker: ChunkSplitter | None = None):
        self.chunker = chunker or ChunkSplitter()

    def parse_to_chunks(
        self,
        file_path: str | Path,
        doc_id: str,
    ) -> list[ParagraphChunk]:
        """
        解析文档并切分为段落块

        Args:
            file_path: 文件路径
            doc_id: 文档 ID（唯一标识）

        Returns:
            段落块列表
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()

        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件类型: {ext}，支持 {SUPPORTED_EXTENSIONS}")

        text, page_map = self._parse_raw(file_path, ext)
        chunks = self.chunker.split(text, doc_id, page_map)

        logger.info(f"文档 {doc_id} ({file_path.name}) 解析完成，生成 {len(chunks)} 个段落块")
        return chunks

    def parse_to_text(self, file_path: str | Path) -> str:
        """仅解析为原始文本（不切分）"""
        file_path = Path(file_path)
        ext = file_path.suffix.lower()
        text, _ = self._parse_raw(file_path, ext)
        return text

    def _parse_raw(self, file_path: Path, ext: str) -> tuple[str, dict[int, int]]:
        """根据扩展名调用对应解析器"""
        if ext == ".pdf":
            from src.document.pdf_parser import PDFParser
            return PDFParser().parse(file_path)
        elif ext in (".docx", ".doc"):
            from src.document.docx_parser import DocxParser
            return DocxParser().parse(file_path)
        elif ext in (".txt", ".text"):
            from src.document.text_parser import TextParser
            return TextParser().parse(file_path)
        else:
            raise ValueError(f"未知文件类型: {ext}")

"""PDF 文档解析（pdfplumber）"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class PDFParser:
    """使用 pdfplumber 解析 PDF，提取文本和页码映射"""

    def parse(self, file_path: str | Path) -> tuple[str, dict[int, int]]:
        """
        解析 PDF 文件

        Returns:
            (full_text, page_map)
            full_text: 完整文本（页间以换行分隔）
            page_map: {char_offset: page_num}
        """
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("请安装 pdfplumber: uv add pdfplumber")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        parts: list[str] = []
        page_map: dict[int, int] = {}
        offset = 0

        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    page_map[offset] = i
                    parts.append(text)
                    offset += len(text) + 2  # +2 for "\n\n"

        full_text = "\n\n".join(parts)
        logger.info(f"PDF 解析完成: {file_path.name}, {len(parts)} 页, {len(full_text)} 字符")
        return full_text, page_map

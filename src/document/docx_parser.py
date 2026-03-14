"""Word 文档解析（python-docx）"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DocxParser:
    """使用 python-docx 解析 .docx 文件，提取段落和表格文本"""

    def parse(self, file_path: str | Path) -> tuple[str, dict[int, int]]:
        """
        解析 .docx 文件

        Returns:
            (full_text, page_map)
            page_map: Word 无精确页码，返回空 dict
        """
        try:
            from docx import Document
        except ImportError:
            raise ImportError("请安装 python-docx: uv add python-docx")

        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        doc = Document(str(file_path))
        parts: list[str] = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                parts.append(text)

        # 提取表格文本
        for table in doc.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    parts.append(" | ".join(cells))

        full_text = "\n\n".join(parts)
        logger.info(f"DOCX 解析完成: {file_path.name}, {len(parts)} 段落, {len(full_text)} 字符")
        return full_text, {}

"""文档段落切分策略"""
import hashlib
import re
from typing import Generator

from src.document.metadata_extractor import MetadataExtractor, ParagraphChunk


def _make_chunk_id(doc_id: str, index: int, text: str) -> str:
    digest = hashlib.md5(f"{doc_id}:{index}:{text[:50]}".encode()).hexdigest()[:8]
    return f"{doc_id}_chunk_{index:04d}_{digest}"


class ChunkSplitter:
    """
    按自然段落边界切分文档文本。
    - 优先按双换行符切分，保留语义完整性
    - 超长段落（>max_chars）使用滑动窗口生成重叠子块
    - 最短段落（<min_chars）跳过
    """

    def __init__(
        self,
        max_chars: int = 800,
        min_chars: int = 50,
        window_size: int = 600,
        step_size: int = 300,
    ):
        self.max_chars = max_chars
        self.min_chars = min_chars
        self.window_size = window_size
        self.step_size = step_size
        self.extractor = MetadataExtractor()

    def split(
        self,
        text: str,
        doc_id: str,
        page_map: dict[int, int] | None = None,
    ) -> list[ParagraphChunk]:
        """
        切分文本为段落块列表

        Args:
            text: 完整文档文本
            doc_id: 文档 ID
            page_map: char_offset -> page_num 映射（可选）
        """
        raw_paragraphs = self._split_paragraphs(text)
        annotated = self.extractor.assign_sections(raw_paragraphs)

        chunks: list[ParagraphChunk] = []
        index = 0

        for para, section in annotated:
            para = para.strip()
            if not para or len(para) < self.min_chars:
                continue

            # 超长段落滑动窗口
            if len(para) > self.max_chars:
                for sub in self._sliding_window(para):
                    chunk = self._make_chunk(sub, doc_id, index, section, page_map, text)
                    chunks.append(chunk)
                    index += 1
            else:
                chunk = self._make_chunk(para, doc_id, index, section, page_map, text)
                chunks.append(chunk)
                index += 1

        return chunks

    def _make_chunk(
        self,
        text: str,
        doc_id: str,
        index: int,
        section_title: str,
        page_map: dict[int, int] | None,
        full_text: str,
    ) -> ParagraphChunk:
        chunk_id = _make_chunk_id(doc_id, index, text)
        page_num = 0
        if page_map:
            # 粗略定位：找文本在全文中的位置
            pos = full_text.find(text[:30])
            if pos >= 0:
                page_num = self._get_page(pos, page_map)

        chunk_type = self.extractor.classify_chunk_type(text)

        return ParagraphChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            text=text,
            page_num=page_num,
            section_title=section_title,
            chunk_type=chunk_type,
            chunk_index=index,
        )

    def _split_paragraphs(self, text: str) -> list[str]:
        """按双换行符或多种分隔符切分"""
        # 统一换行符
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # 按双换行或分隔线切分
        paras = re.split(r"\n{2,}|(?:^[-=─━]{3,}\s*$)", text, flags=re.MULTILINE)
        return [p.strip() for p in paras if p.strip()]

    def _sliding_window(self, text: str) -> Generator[str, None, None]:
        """滑动窗口切分超长段落"""
        start = 0
        while start < len(text):
            end = min(start + self.window_size, len(text))
            yield text[start:end]
            if end >= len(text):
                break
            start += self.step_size

    @staticmethod
    def _get_page(char_pos: int, page_map: dict[int, int]) -> int:
        """根据字符位置查找页码"""
        page = 0
        for offset, pg in sorted(page_map.items()):
            if char_pos >= offset:
                page = pg
            else:
                break
        return page

"""文档段落切分策略"""
import hashlib
import re
from typing import Generator

from src.document.docx_parser import HEADING_MARKER
from src.document.metadata_extractor import MetadataExtractor, ParagraphChunk

# 短段落列表项合并上限（条）
_LIST_MERGE_MAX = 5
# 合并后最小字数（低于此丢弃）
_MERGED_MIN_CHARS = 10


def _make_chunk_id(doc_id: str, index: int, text: str) -> str:
    digest = hashlib.md5(f"{doc_id}:{index}:{text[:50]}".encode()).hexdigest()[:8]
    return f"{doc_id}_chunk_{index:04d}_{digest}"


class ChunkSplitter:
    """
    按自然段落边界切分文档文本。

    改进：
    - 章节标题（§H§ 前缀）始终保留，不做长度过滤
    - 分级 min_chars：legal_ref/standard_ref=10，普通段落=min_chars（默认 20）
    - 连续短段落（<40 字）合并为列表 chunk（上限 5 条）
    - 超长段落优先按句子边界切分，保证语义完整性
    """

    def __init__(
        self,
        max_chars: int = 800,
        min_chars: int = 20,
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
            text: 完整文档文本（可含 §H§ 标记）
            doc_id: 文档 ID
            page_map: char_offset -> page_num 映射（可选）
        """
        raw_paragraphs = self._split_paragraphs(text)

        # 识别 heading 标记并剥离前缀
        paras_info: list[tuple[str, bool]] = []  # (text, is_heading)
        for p in raw_paragraphs:
            if p.startswith(HEADING_MARKER):
                paras_info.append((p[len(HEADING_MARKER):], True))
            else:
                paras_info.append((p, False))

        plain_texts = [p for p, _ in paras_info]
        section_assignments = self.extractor.assign_sections(plain_texts)

        chunks: list[ParagraphChunk] = []
        index = 0

        # 短段落列表合并缓冲区
        list_buffer: list[tuple[str, str]] = []  # (text, section)
        list_buffer_section: str = ""

        def flush_buffer() -> None:
            nonlocal index
            if not list_buffer:
                return
            merged_chunks = self._merge_list_items(
                list_buffer, doc_id, index, list_buffer_section, page_map, text
            )
            chunks.extend(merged_chunks)
            index += len(merged_chunks)
            list_buffer.clear()

        for (para, section), (_, is_heading) in zip(section_assignments, paras_info):
            para = para.strip()
            if not para:
                continue

            # 章节标题：始终保留
            if is_heading:
                flush_buffer()
                chunk = self._make_chunk(
                    para, doc_id, index, section, page_map, text, is_heading=True
                )
                chunks.append(chunk)
                index += 1
                continue

            chunk_type = self.extractor.classify_chunk_type(para)
            effective_min = self._get_min_chars(chunk_type)

            if len(para) < effective_min:
                # 短段落：加入列表合并缓冲
                if list_buffer and list_buffer_section != section:
                    flush_buffer()
                list_buffer.append((para, section))
                list_buffer_section = section
                continue
            else:
                # 当前段落不短时，先刷出缓冲
                if list_buffer:
                    flush_buffer()

            # 超长段落：按句子边界切分
            if len(para) > self.max_chars:
                for sub in self._sentence_split(para):
                    c = self._make_chunk(sub, doc_id, index, section, page_map, text)
                    chunks.append(c)
                    index += 1
            else:
                chunk = self._make_chunk(para, doc_id, index, section, page_map, text)
                chunks.append(chunk)
                index += 1

        # 最终刷出缓冲
        flush_buffer()

        return chunks

    # ── 辅助方法 ──────────────────────────────────────────────────

    def _get_min_chars(self, chunk_type: str) -> int:
        """根据 chunk 类型返回有效最小字数"""
        if chunk_type in ("legal_ref", "standard_ref"):
            return 10
        return self.min_chars

    def _merge_list_items(
        self,
        buffer: list[tuple[str, str]],
        doc_id: str,
        start_index: int,
        section: str,
        page_map: dict[int, int] | None,
        full_text: str,
    ) -> list[ParagraphChunk]:
        """将缓冲中的短段落按 _LIST_MERGE_MAX 分组合并"""
        result: list[ParagraphChunk] = []
        idx = start_index
        i = 0
        while i < len(buffer):
            group = buffer[i : i + _LIST_MERGE_MAX]
            merged_text = "\n".join(p for p, _ in group).strip()
            if len(merged_text) >= _MERGED_MIN_CHARS:
                chunk = self._make_chunk(
                    merged_text, doc_id, idx, section, page_map, full_text
                )
                result.append(chunk)
                idx += 1
            i += _LIST_MERGE_MAX
        return result

    def _make_chunk(
        self,
        text: str,
        doc_id: str,
        index: int,
        section_title: str,
        page_map: dict[int, int] | None,
        full_text: str,
        is_heading: bool = False,
    ) -> ParagraphChunk:
        chunk_id = _make_chunk_id(doc_id, index, text)
        page_num = 0
        if page_map:
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
            is_heading=is_heading,
            chunk_index=index,
        )

    def _split_paragraphs(self, text: str) -> list[str]:
        """按双换行符或分隔线切分"""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        paras = re.split(r"\n{2,}|(?:^[-=─━]{3,}\s*$)", text, flags=re.MULTILINE)
        return [p.strip() for p in paras if p.strip()]

    def _sentence_split(self, text: str) -> Generator[str, None, None]:
        """
        优先按句子边界（。；！？）切分超长段落，
        单句仍超长时回退到滑动窗口。
        """
        parts = re.split(r"(?<=[。；！？])", text)
        current = ""
        for part in parts:
            if not part.strip():
                continue
            if len(current) + len(part) <= self.window_size:
                current += part
            else:
                if current:
                    stripped = current.strip()
                    if len(stripped) >= self.min_chars:
                        yield stripped
                    elif len(stripped) >= _MERGED_MIN_CHARS:
                        yield stripped
                current = part
        if current:
            stripped = current.strip()
            if len(stripped) >= _MERGED_MIN_CHARS:
                yield stripped

    def _sliding_window(self, text: str) -> Generator[str, None, None]:
        """滑动窗口切分（备用）"""
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

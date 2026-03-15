"""文档结构相似度分析：对比两份文档的章节标题列表"""
import difflib
import logging
from dataclasses import dataclass, field

from src.document.metadata_extractor import ParagraphChunk

logger = logging.getLogger(__name__)

HEADING_MARKER = "§H§"


@dataclass
class StructureSimilarity:
    title_jaccard: float                              # 章节标题集合 Jaccard 相似度
    sequence_similarity: float                        # 标题顺序相似度（基于编辑距离）
    matched_sections: list[tuple[str, str]] = field(default_factory=list)  # 匹配的标题对
    structure_risk_level: str = "none"               # "high" / "medium" / "low" / "none"
    overall_score: float = 0.0                       # 0-100


class StructureComparator:
    """比较两份文档的章节结构相似度"""

    def _extract_headings(self, chunks: list[ParagraphChunk]) -> list[str]:
        """从 chunks 中提取标题文本（去除 §H§ 前缀）"""
        headings = []
        for chunk in chunks:
            if chunk.is_heading:
                text = chunk.text
                if text.startswith(HEADING_MARKER):
                    text = text[len(HEADING_MARKER):].strip()
                if text:
                    headings.append(text)
        return headings

    def _jaccard(self, set_a: set[str], set_b: set[str]) -> float:
        if not set_a and not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    def _sequence_similarity(self, list_a: list[str], list_b: list[str]) -> float:
        if not list_a and not list_b:
            return 0.0
        return difflib.SequenceMatcher(None, list_a, list_b).ratio()

    def _find_matched_sections(self, list_a: list[str], list_b: list[str]) -> list[tuple[str, str]]:
        """找出最长公共子序列中的匹配标题对"""
        matcher = difflib.SequenceMatcher(None, list_a, list_b)
        matched = []
        for block in matcher.get_matching_blocks():
            i, j, size = block
            for k in range(size):
                matched.append((list_a[i + k], list_b[j + k]))
        return matched

    def compare(self, chunks_a: list[ParagraphChunk], chunks_b: list[ParagraphChunk]) -> StructureSimilarity:
        """比较两份文档的章节结构，返回 StructureSimilarity"""
        headings_a = self._extract_headings(chunks_a)
        headings_b = self._extract_headings(chunks_b)

        logger.info(f"结构分析: 文档A {len(headings_a)} 个标题, 文档B {len(headings_b)} 个标题")

        if not headings_a or not headings_b:
            return StructureSimilarity(
                title_jaccard=0.0,
                sequence_similarity=0.0,
                matched_sections=[],
                structure_risk_level="none",
                overall_score=0.0,
            )

        jaccard = self._jaccard(set(headings_a), set(headings_b))
        seq_sim = self._sequence_similarity(headings_a, headings_b)
        overall_score = round((0.5 * jaccard + 0.5 * seq_sim) * 100, 2)
        matched = self._find_matched_sections(headings_a, headings_b)

        if overall_score >= 70:
            risk_level = "high"
        elif overall_score >= 50:
            risk_level = "medium"
        elif overall_score >= 30:
            risk_level = "low"
        else:
            risk_level = "none"

        logger.info(f"结构相似度: jaccard={jaccard:.3f}, seq={seq_sim:.3f}, score={overall_score}, 风险={risk_level}")

        return StructureSimilarity(
            title_jaccard=round(jaccard, 4),
            sequence_similarity=round(seq_sim, 4),
            matched_sections=matched,
            structure_risk_level=risk_level,
            overall_score=overall_score,
        )

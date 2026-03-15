"""风险评分：综合向量相似度 + 关键词重叠"""
import logging
from dataclasses import dataclass, field
from typing import Literal

from src.analysis.keyword_extractor import KeywordExtractor
from src.document.metadata_extractor import ParagraphChunk

logger = logging.getLogger(__name__)

RiskLevel = Literal["high", "medium", "low", "none"]


@dataclass
class SimilarPair:
    """相似段落对"""
    pair_id: str
    chunk_a: ParagraphChunk
    chunk_b: ParagraphChunk
    vector_similarity: float
    keyword_overlap: float = 0.0
    context_bonus: float = 0.0
    base_risk_score: float = 0.0
    llm_adjustment: float = 0.0
    final_score: float = 0.0
    risk_level: RiskLevel = "none"
    risk_type: str = "normal_overlap"
    confidence: float = 0.0
    reason_zh: str = ""
    evidence_quote_a: str = ""
    evidence_quote_b: str = ""
    suggest_action: str = ""
    metadata: dict = field(default_factory=dict)


class RiskScorer:
    """
    综合风险评分器

    评分公式:
        base_risk_score = (
            vector_similarity × 0.60 +
            keyword_overlap × 0.25 +
            context_bonus × 0.15
        ) × 100
        白名单惩罚: × 0.50
        最终分 = base_risk_score + llm_adjustment
    """

    WEIGHTS = {
        "vector": 0.60,
        "keyword": 0.25,
        "context": 0.15,
    }
    CONTEXT_BONUS_SAME_SECTION = 0.10
    CONTEXT_BONUS_TECH_SPEC = 0.05
    WHITELIST_PENALTY = 0.50

    THRESHOLDS = {
        "high": 85.0,
        "medium": 65.0,
        "low": 45.0,
    }

    def __init__(self, keyword_extractor: KeywordExtractor | None = None):
        self.keyword_extractor = keyword_extractor or KeywordExtractor()

    def score_pair(self, chunk_a: ParagraphChunk, chunk_b: ParagraphChunk, vector_similarity: float) -> SimilarPair:
        """计算一对段落的综合风险分"""
        import hashlib
        pair_id = hashlib.md5(
            f"{chunk_a.chunk_id}:{chunk_b.chunk_id}".encode()
        ).hexdigest()[:12]

        # 关键词 Jaccard 相似度
        keyword_overlap = self.keyword_extractor.jaccard_similarity(chunk_a.text, chunk_b.text)

        # 上下文加分
        context_bonus = 0.0
        if chunk_a.section_title and chunk_a.section_title == chunk_b.section_title:
            context_bonus += self.CONTEXT_BONUS_SAME_SECTION
        if chunk_a.chunk_type == "tech_spec" and chunk_b.chunk_type == "tech_spec":
            context_bonus += self.CONTEXT_BONUS_TECH_SPEC

        # base_risk_score
        raw_score = (
            vector_similarity * self.WEIGHTS["vector"] +
            keyword_overlap * self.WEIGHTS["keyword"] +
            context_bonus * self.WEIGHTS["context"]
        ) * 100

        # 白名单惩罚
        if chunk_a.is_whitelisted or chunk_b.is_whitelisted:
            raw_score *= self.WHITELIST_PENALTY

        pair = SimilarPair(
            pair_id=pair_id,
            chunk_a=chunk_a,
            chunk_b=chunk_b,
            vector_similarity=vector_similarity,
            keyword_overlap=keyword_overlap,
            context_bonus=context_bonus,
            base_risk_score=round(raw_score, 2),
            final_score=round(raw_score, 2),
        )
        pair.risk_level = self._level(raw_score)
        return pair

    def apply_llm_adjustment(self, pair: SimilarPair, adjustment: float) -> SimilarPair:
        """应用 LLM 调整值，重新计算最终分和风险等级"""
        adjustment = max(-20.0, min(20.0, adjustment))
        pair.llm_adjustment = adjustment
        pair.final_score = round(pair.base_risk_score + adjustment, 2)
        pair.risk_level = self._level(pair.final_score)
        return pair

    def compute_overall_risk(
        self,
        scored_pairs: list[SimilarPair],
        total_chunks_a: int,
    ) -> tuple[str, float]:
        """
        计算整体文档风险等级和雷同率

        Returns:
            (overall_risk_level, similarity_rate)
        """
        high_pairs = [p for p in scored_pairs if p.risk_level == "high"]
        medium_pairs = [p for p in scored_pairs if p.risk_level == "medium"]
        low_pairs = [p for p in scored_pairs if p.risk_level == "low"]

        # 计算所有风险对（high/medium/low）覆盖的不重叠段落数
        covered_chunks: set[str] = set()
        for p in high_pairs + medium_pairs + low_pairs:
            covered_chunks.add(p.chunk_a.chunk_id)

        similarity_rate = len(covered_chunks) / total_chunks_a if total_chunks_a > 0 else 0.0
        total_scored = len(scored_pairs)
        high_ratio = len(high_pairs) / total_scored if total_scored > 0 else 0.0

        if similarity_rate >= 0.30 or high_ratio >= 0.05:
            level = "high"
        elif similarity_rate >= 0.15 or (len(high_pairs) >= 1 and len(medium_pairs) >= 3):
            level = "medium"
        else:
            level = "low"

        return level, round(similarity_rate, 4)

    @classmethod
    def _level(cls, score: float) -> RiskLevel:
        if score >= cls.THRESHOLDS["high"]:
            return "high"
        elif score >= cls.THRESHOLDS["medium"]:
            return "medium"
        elif score >= cls.THRESHOLDS["low"]:
            return "low"
        else:
            return "none"

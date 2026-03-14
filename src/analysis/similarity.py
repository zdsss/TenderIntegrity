"""SimilarityEngine：向量检索 + 关键词相似度"""
import logging
from itertools import combinations

from src.analysis.scorer import RiskScorer, SimilarPair
from src.document.metadata_extractor import ParagraphChunk
from src.vectorstore.repository import ChromaRepository

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """跨文档相似度检索引擎"""

    def __init__(
        self,
        chroma_repo: ChromaRepository,
        scorer: RiskScorer | None = None,
        top_k: int = 5,
        min_similarity: float = 0.70,
    ):
        self.chroma_repo = chroma_repo
        self.scorer = scorer or RiskScorer()
        self.top_k = top_k
        self.min_similarity = min_similarity

    def find_similar_pairs(
        self,
        chunks_by_doc: dict[str, list[ParagraphChunk]],
        task_id: str,
        mode: str = "pairwise",
    ) -> list[SimilarPair]:
        """
        在多个文档间检索相似段落对

        Args:
            chunks_by_doc: {doc_id: [ParagraphChunk, ...]}
            task_id: 任务 ID
            mode: "pairwise"（仅第1对）或 "all_vs_all"（所有组合）

        Returns:
            候选相似对列表（按 vector_similarity 降序）
        """
        doc_ids = list(chunks_by_doc.keys())
        if len(doc_ids) < 2:
            return []

        if mode == "pairwise":
            pairs_to_compare = [(doc_ids[0], doc_ids[1])]
        else:
            pairs_to_compare = list(combinations(doc_ids, 2))

        all_pairs: list[SimilarPair] = []
        seen_pairs: set[str] = set()

        for doc_id_a, doc_id_b in pairs_to_compare:
            chunks_a = chunks_by_doc[doc_id_a]
            logger.info(f"检索相似对: {doc_id_a} <-> {doc_id_b}, {len(chunks_a)} 个块")

            for chunk_a in chunks_a:
                # 跳过白名单段落
                if chunk_a.is_whitelisted:
                    continue

                hits = self.chroma_repo.query_similar(
                    query_chunk=chunk_a,
                    exclude_doc_id=doc_id_a,
                    task_id=task_id,
                    top_k=self.top_k,
                    min_similarity=self.min_similarity,
                )

                for hit in hits:
                    # 构建对应的 ParagraphChunk（简化版）
                    meta = hit.get("metadata", {})
                    chunk_b = ParagraphChunk(
                        chunk_id=hit["chunk_id"],
                        doc_id=hit["doc_id"],
                        text=hit["text"],
                        page_num=int(meta.get("page_num", 0)),
                        section_title=meta.get("section_title", ""),
                        chunk_type=meta.get("chunk_type", "normal"),  # type: ignore
                        is_whitelisted=meta.get("is_whitelisted", "False") == "True",
                    )

                    # 去重
                    key = ":".join(sorted([chunk_a.chunk_id, chunk_b.chunk_id]))
                    if key in seen_pairs:
                        continue
                    seen_pairs.add(key)

                    pair = self.scorer.score_pair(chunk_a, chunk_b, hit["similarity"])
                    all_pairs.append(pair)

        # 按 base_risk_score 降序
        all_pairs.sort(key=lambda p: p.base_risk_score, reverse=True)
        logger.info(f"共发现 {len(all_pairs)} 个候选相似对")
        return all_pairs

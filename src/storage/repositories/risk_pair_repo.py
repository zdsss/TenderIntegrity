"""风险对仓库"""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.analysis.scorer import SimilarPair
from src.storage.models import RiskPair


class RiskPairRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_from_pair(self, task_id: str, pair: SimilarPair) -> RiskPair:
        rp = RiskPair(
            id=str(uuid.uuid4()),
            task_id=task_id,
            pair_id=pair.pair_id,
            risk_level=pair.risk_level,
            risk_type=pair.risk_type,
            final_score=pair.final_score,
            vector_similarity=pair.vector_similarity,
            keyword_overlap=pair.keyword_overlap,
            confidence=pair.confidence,
            doc_a_id=pair.chunk_a.doc_id,
            doc_b_id=pair.chunk_b.doc_id,
            chunk_a_id=pair.chunk_a.chunk_id,
            chunk_b_id=pair.chunk_b.chunk_id,
            section_a=pair.chunk_a.section_title,
            section_b=pair.chunk_b.section_title,
            text_a=pair.chunk_a.text,
            text_b=pair.chunk_b.text,
            reason_zh=pair.reason_zh,
            suggest_action=pair.suggest_action,
        )
        self.session.add(rp)
        await self.session.flush()
        return rp

    async def get_by_task(self, task_id: str, risk_level: str | None = None) -> list[RiskPair]:
        query = select(RiskPair).where(RiskPair.task_id == task_id)
        if risk_level:
            query = query.where(RiskPair.risk_level == risk_level)
        query = query.order_by(RiskPair.final_score.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

"""score_candidates 节点"""
import logging
from config.settings import settings
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def score_candidates(state: TenderComparisonState) -> dict:
    all_pairs = state["candidate_pairs"]
    low_risk_threshold = settings.low_risk_threshold
    scored_pairs = [p for p in all_pairs if p.base_risk_score >= low_risk_threshold]
    logger.info(f"风险评分过滤: {len(all_pairs)} -> {len(scored_pairs)} 对 (阈值 {low_risk_threshold})")
    return {"scored_pairs": scored_pairs, "current_node": "score_candidates", "processing_progress": 0.75}

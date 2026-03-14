"""llm_analyze_pairs 节点"""
import logging
from config.settings import settings
from src.chains.risk_reason_chain import RiskReasonChain
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def llm_analyze_pairs(state: TenderComparisonState) -> dict:
    scored_pairs = state["scored_pairs"]
    to_analyze = [p for p in scored_pairs if p.base_risk_score >= settings.medium_risk_threshold]
    no_analyze = [p for p in scored_pairs if p.base_risk_score < settings.medium_risk_threshold]
    logger.info(f"LLM 分析: {len(to_analyze)} 个高/中风险对")
    chain = RiskReasonChain(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        anthropic_api_key=settings.anthropic_api_key or None,
        provider=settings.llm_provider,
        openai_api_key=settings.dashscope_api_key or None,
        openai_base_url=settings.dashscope_base_url or None,
    )
    doc_names = state.get("doc_names", {})
    analyzed_pairs = chain.batch_analyze(to_analyze, doc_names)
    all_pairs = analyzed_pairs + no_analyze
    all_pairs.sort(key=lambda p: p.final_score, reverse=True)
    logger.info(f"LLM 分析完成，共 {len(all_pairs)} 对")
    return {"llm_analyzed_pairs": all_pairs, "current_node": "llm_analyze_pairs", "processing_progress": 0.90}

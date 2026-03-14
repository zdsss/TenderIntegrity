"""条件路由函数"""
from src.workflow.state import TenderComparisonState


def route_after_score(state: TenderComparisonState) -> str:
    scored_pairs = state.get("scored_pairs", [])
    if not scored_pairs:
        return "generate_report"
    from config.settings import settings
    has_medium_or_high = any(
        p.base_risk_score >= settings.medium_risk_threshold for p in scored_pairs
    )
    return "llm_analyze_pairs" if has_medium_or_high else "generate_report"

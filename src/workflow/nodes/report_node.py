"""generate_report 节点"""
import logging
from src.analysis.scorer import RiskScorer
from src.analysis.risk_synthesizer import RiskSynthesizer
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def generate_report(state: TenderComparisonState) -> dict:
    pairs = state.get("llm_analyzed_pairs") or state.get("scored_pairs") or []
    total_chunks_a = 0
    if state["chunks"]:
        first_doc_id = state["doc_ids"][0] if state["doc_ids"] else next(iter(state["chunks"]))
        total_chunks_a = len(state["chunks"].get(first_doc_id, []))

    # 文本维度风险（原始）
    scorer = RiskScorer()
    text_risk_level, overall_similarity_rate = scorer.compute_overall_risk(pairs, total_chunks_a)

    # 综合风险合成（Q5：整合多维度信号）
    synthesizer = RiskSynthesizer()
    composite = synthesizer.synthesize(
        text_level=text_risk_level,
        text_rate=overall_similarity_rate,
        structure=state.get("structure_similarity"),
        field_overlaps=state.get("field_overlaps") or [],
        rare_token=state.get("rare_token_analysis"),
        price=state.get("price_analysis"),
        meta=state.get("meta_comparison"),
    )
    overall_risk_level = composite.final_level

    high_pairs = [p for p in pairs if p.risk_level == "high"]
    medium_pairs = [p for p in pairs if p.risk_level == "medium"]
    low_pairs = [p for p in pairs if p.risk_level == "low"]

    risk_pairs_data = []
    for pair in pairs:
        if pair.risk_level == "none":
            continue
        risk_pairs_data.append({
            "pair_id": pair.pair_id,
            "risk_level": pair.risk_level,
            "risk_type": pair.risk_type,
            "final_score": pair.final_score,
            "base_risk_score": pair.base_risk_score,
            "vector_similarity": round(pair.vector_similarity, 4),
            "keyword_overlap": round(pair.keyword_overlap, 4),
            "doc_a": {
                "doc_id": pair.chunk_a.doc_id,
                "chunk_id": pair.chunk_a.chunk_id,
                "section": pair.chunk_a.section_title,
                "page": pair.chunk_a.page_num,
                "text": pair.chunk_a.text,
                "chunk_type": pair.chunk_a.chunk_type,
            },
            "doc_b": {
                "doc_id": pair.chunk_b.doc_id,
                "chunk_id": pair.chunk_b.chunk_id,
                "section": pair.chunk_b.section_title,
                "page": pair.chunk_b.page_num,
                "text": pair.chunk_b.text,
                "chunk_type": pair.chunk_b.chunk_type,
            },
            "confidence": pair.confidence,
            "reason_zh": pair.reason_zh,
            "evidence_quote_a": pair.evidence_quote_a,
            "evidence_quote_b": pair.evidence_quote_b,
            "suggest_action": pair.suggest_action,
        })

    report = {
        "task_id": state["task_id"],
        "overall_risk_level": overall_risk_level,
        "overall_similarity_rate": overall_similarity_rate,
        "risk_summary": {
            "high_count": len(high_pairs),
            "medium_count": len(medium_pairs),
            "low_count": len(low_pairs),
            "total_count": len(pairs),
        },
        "doc_info": {
            doc_id: {
                "filename": state.get("doc_names", {}).get(doc_id, doc_id),
                "chunk_count": len(chunks),
            }
            for doc_id, chunks in state["chunks"].items()
        },
        "risk_pairs": risk_pairs_data,
        "structure_analysis": state.get("structure_similarity"),
        "field_overlaps": state.get("field_overlaps") or [],
        "rare_token_analysis": state.get("rare_token_analysis"),
        "price_analysis": state.get("price_analysis"),
        "meta_comparison": state.get("meta_comparison"),
        "composite_risk": {
            "final_level": composite.final_level,
            "text_risk_level": composite.text_risk_level,
            "triggered_signals": composite.triggered_signals,
            "signal_breakdown": composite.signal_breakdown,
        },
    }

    logger.info(
        f"报告生成完成: 文本风险={text_risk_level}, 综合风险={overall_risk_level}, "
        f"雷同率={overall_similarity_rate:.1%}, 触发信号={len(composite.triggered_signals)}"
    )
    return {
        "report": report,
        "overall_risk_level": overall_risk_level,
        "overall_similarity_rate": overall_similarity_rate,
        "current_node": "generate_report",
        "processing_progress": 1.0,
    }

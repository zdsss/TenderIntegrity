"""报告相关 Pydantic 模型"""
from pydantic import BaseModel


class RiskPairDetail(BaseModel):
    pair_id: str
    risk_level: str
    risk_type: str
    final_score: float
    vector_similarity: float
    keyword_overlap: float
    doc_a: dict
    doc_b: dict
    reason_zh: str
    suggest_action: str
    confidence: float


class RiskReportResponse(BaseModel):
    task_id: str
    overall_risk_level: str
    overall_similarity_rate: float
    risk_summary: dict
    risk_pairs: list[RiskPairDetail]

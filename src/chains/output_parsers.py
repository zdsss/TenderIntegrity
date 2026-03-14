"""Pydantic 结构化输出解析器"""
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class RiskAnalysisOutput(BaseModel):
    """LLM 风险分析输出结构"""

    risk_level: Literal["high", "medium", "low", "none"] = Field(
        description="风险等级"
    )
    risk_type: Literal[
        "verbatim_copy",
        "semantic_paraphrase",
        "template_reuse",
        "key_param_duplicate",
        "normal_overlap",
    ] = Field(description="风险类型")
    confidence: float = Field(ge=0.0, le=1.0, description="置信度 0~1")
    reason_zh: str = Field(description="中文判定理由（100~200字）")
    evidence_quote_a: str = Field(default="", description="文档A关键证据引用")
    evidence_quote_b: str = Field(default="", description="文档B关键证据引用")
    suggest_action: str = Field(default="", description="建议复核行动")
    score_adjustment: float = Field(
        default=0.0,
        ge=-20.0,
        le=20.0,
        description="对 base_risk_score 的调整（-20~+20）",
    )

    @field_validator("reason_zh")
    @classmethod
    def validate_reason_length(cls, v: str) -> str:
        if len(v) < 20:
            raise ValueError("判定理由至少 20 字")
        return v

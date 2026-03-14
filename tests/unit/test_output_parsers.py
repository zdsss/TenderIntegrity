"""RiskAnalysisOutput 解析器单元测试"""
import pytest
from src.chains.output_parsers import RiskAnalysisOutput


def test_valid_output():
    output = RiskAnalysisOutput(
        risk_level="high",
        risk_type="verbatim_copy",
        confidence=0.95,
        reason_zh="两段文字几乎完全相同，技术参数描述逐字复制，属于典型的逐字抄袭行为，存在极高的围标风险。",
        evidence_quote_a="分辨率1024×1024像素",
        evidence_quote_b="分辨率1024×1024像素",
        suggest_action="建议重点复核技术方案章节",
        score_adjustment=15.0,
    )
    assert output.risk_level == "high"
    assert output.confidence == 0.95
    assert output.score_adjustment == 15.0


def test_score_adjustment_clamp():
    with pytest.raises(ValueError):
        RiskAnalysisOutput(
            risk_level="high",
            risk_type="verbatim_copy",
            confidence=0.9,
            reason_zh="测试判定理由内容超过二十字符的要求长度",
            score_adjustment=25.0,  # 超过最大值 +20
        )


def test_reason_too_short():
    with pytest.raises(ValueError):
        RiskAnalysisOutput(
            risk_level="low",
            risk_type="normal_overlap",
            confidence=0.5,
            reason_zh="太短",  # 少于 20 字
            score_adjustment=0.0,
        )


def test_confidence_range():
    with pytest.raises(ValueError):
        RiskAnalysisOutput(
            risk_level="medium",
            risk_type="semantic_paraphrase",
            confidence=1.5,  # 超过 1.0
            reason_zh="测试判定理由需要足够长度超过二十字符的要求",
            score_adjustment=0.0,
        )

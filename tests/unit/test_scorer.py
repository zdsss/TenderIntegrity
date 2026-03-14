"""RiskScorer 单元测试"""
import pytest
from src.analysis.scorer import RiskScorer, SimilarPair
from src.document.metadata_extractor import ParagraphChunk


def make_chunk(doc_id, text, section="", chunk_type="normal", is_whitelisted=False):
    return ParagraphChunk(
        chunk_id=f"{doc_id}_test",
        doc_id=doc_id,
        text=text,
        section_title=section,
        chunk_type=chunk_type,
        is_whitelisted=is_whitelisted,
    )


@pytest.fixture
def scorer():
    return RiskScorer()


def test_high_similarity_score(scorer):
    chunk_a = make_chunk("doc_a", "医疗设备技术参数：分辨率1024x1024，帧率25fps，探头频率5MHz")
    chunk_b = make_chunk("doc_b", "医疗设备技术参数：分辨率1024x1024，帧率25fps，探头频率5MHz")
    pair = scorer.score_pair(chunk_a, chunk_b, vector_similarity=0.95)
    assert pair.base_risk_score > 50  # 高相似度应有较高分数
    assert pair.risk_level in ("high", "medium", "low")


def test_whitelist_penalty(scorer):
    chunk_a = make_chunk("doc_a", "投标人应当按照采购文件要求提交投标文件", is_whitelisted=True)
    chunk_b = make_chunk("doc_b", "投标方须按照采购文件要求提交投标文件", is_whitelisted=True)
    pair = scorer.score_pair(chunk_a, chunk_b, vector_similarity=0.95)
    # 白名单惩罚应大幅降低分数
    assert pair.base_risk_score < 25  # 0.95*100*0.2 ≈ 19


def test_context_bonus_same_section(scorer):
    chunk_a = make_chunk("doc_a", "技术参数详细说明内容", section="技术方案", chunk_type="tech_spec")
    chunk_b = make_chunk("doc_b", "技术参数详细说明内容", section="技术方案", chunk_type="tech_spec")
    pair = scorer.score_pair(chunk_a, chunk_b, vector_similarity=0.80)
    # 同章节 +0.1，tech_spec +0.05 = +0.15
    # base = (0.80*0.60 + kw_overlap*0.25 + 0.15*0.15)*100
    assert pair.base_risk_score > 0.80 * 60  # 大于纯向量分


def test_risk_levels(scorer):
    assert scorer._level(90) == "high"
    assert scorer._level(70) == "medium"
    assert scorer._level(50) == "low"
    assert scorer._level(30) == "none"


def test_llm_adjustment(scorer):
    chunk_a = make_chunk("doc_a", "测试段落")
    chunk_b = make_chunk("doc_b", "测试段落")
    pair = scorer.score_pair(chunk_a, chunk_b, vector_similarity=0.80)
    original_score = pair.base_risk_score

    scorer.apply_llm_adjustment(pair, 15.0)
    assert pair.final_score == pytest.approx(original_score + 15.0, abs=0.1)

    # 测试边界钳制
    scorer.apply_llm_adjustment(pair, 100.0)  # 超过最大值
    assert pair.llm_adjustment == pytest.approx(20.0, abs=0.1)


def test_overall_risk(scorer):
    chunk_a = make_chunk("doc_a", "text")
    chunk_b = make_chunk("doc_b", "text")

    # 3+ 高风险 → high
    high_pairs = []
    for i in range(3):
        p = scorer.score_pair(
            ParagraphChunk(chunk_id=f"a_{i}", doc_id="doc_a", text="t"),
            chunk_b,
            vector_similarity=0.95,
        )
        p.risk_level = "high"
        p.base_risk_score = 90.0
        p.final_score = 90.0
        high_pairs.append(p)

    level, rate = scorer.compute_overall_risk(high_pairs, total_chunks_a=10)
    assert level == "high"

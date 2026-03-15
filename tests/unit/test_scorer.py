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
    # 白名单惩罚 ×0.50 应降低分数（约 0.95*60*0.5 ≈ 28.5，加上关键词和上下文后 < 55）
    assert pair.base_risk_score < 55


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
    chunk_b = make_chunk("doc_b", "text")

    # 高风险对占比 >= 5% → high
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
    # 3 高风险对占 3/3=100% → high_ratio=1.0 >= 0.05
    assert rate > 0


def test_similarity_rate_includes_all_risk_levels(scorer):
    """similarity_rate 应覆盖 high/medium/low 所有风险对（P1 修复验证）"""
    chunk_b = make_chunk("doc_b", "text")

    # 构造 5 个 medium 对 + 0 个 high 对，total_chunks_a=20
    medium_pairs = []
    for i in range(5):
        p = scorer.score_pair(
            ParagraphChunk(chunk_id=f"med_{i}", doc_id="doc_a", text="t"),
            chunk_b,
            vector_similarity=0.70,
        )
        p.risk_level = "medium"
        medium_pairs.append(p)

    _, rate = scorer.compute_overall_risk(medium_pairs, total_chunks_a=20)
    # 5 个不同 chunk_id 覆盖 5/20 = 0.25
    assert rate == pytest.approx(0.25, abs=0.01)


def test_overall_risk_ratio_based(scorer):
    """整体风险应基于覆盖比例而非绝对数量（P2 修复验证）"""
    chunk_b = make_chunk("doc_b", "text")

    # 20 chunk 文档，6 个 medium 对 → similarity_rate=0.30 → high
    pairs = []
    for i in range(6):
        p = scorer.score_pair(
            ParagraphChunk(chunk_id=f"m_{i}", doc_id="doc_a", text="t"),
            chunk_b,
            vector_similarity=0.70,
        )
        p.risk_level = "medium"
        pairs.append(p)

    level, rate = scorer.compute_overall_risk(pairs, total_chunks_a=20)
    assert rate == pytest.approx(0.30, abs=0.01)
    assert level == "high"  # similarity_rate=0.30 >= threshold

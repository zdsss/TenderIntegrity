"""StructureComparator 单元测试"""
import pytest
from src.analysis.structure_comparator import StructureComparator
from src.document.metadata_extractor import ParagraphChunk


def make_heading(chunk_id: str, text: str, doc_id: str = "doc_a") -> ParagraphChunk:
    return ParagraphChunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=f"§H§{text}",
        is_heading=True,
    )


def make_normal(chunk_id: str, text: str, doc_id: str = "doc_a") -> ParagraphChunk:
    return ParagraphChunk(
        chunk_id=chunk_id,
        doc_id=doc_id,
        text=text,
        is_heading=False,
    )


@pytest.fixture
def comparator():
    return StructureComparator()


def test_identical_structure(comparator):
    """完全相同的章节结构应给出高风险"""
    titles = ["第一章 总则", "第二章 投标要求", "第三章 技术规格", "第四章 商务条款"]
    chunks_a = [make_heading(f"a_{i}", t) for i, t in enumerate(titles)]
    chunks_b = [make_heading(f"b_{i}", t, "doc_b") for i, t in enumerate(titles)]
    result = comparator.compare(chunks_a, chunks_b)
    assert result.title_jaccard == pytest.approx(1.0, abs=0.01)
    assert result.sequence_similarity == pytest.approx(1.0, abs=0.01)
    assert result.overall_score == pytest.approx(100.0, abs=0.1)
    assert result.structure_risk_level == "high"


def test_empty_headings(comparator):
    """无标题时返回 none 风险"""
    chunks_a = [make_normal("a_0", "正文内容")]
    chunks_b = [make_normal("b_0", "另一份正文")]
    result = comparator.compare(chunks_a, chunks_b)
    assert result.structure_risk_level == "none"
    assert result.overall_score == 0.0


def test_different_structure(comparator):
    """完全不同的结构应给出低或无风险"""
    chunks_a = [make_heading(f"a_{i}", f"章节{i}") for i in range(5)]
    chunks_b = [make_heading(f"b_{i}", f"部分{i}", "doc_b") for i in range(5)]
    result = comparator.compare(chunks_a, chunks_b)
    assert result.title_jaccard == 0.0
    assert result.structure_risk_level in ("none", "low")


def test_partial_overlap(comparator):
    """部分章节相同应给出中等风险"""
    titles_a = ["第一章 总则", "第二章 资质要求", "第三章 技术参数", "第四章 商务条款"]
    titles_b = ["第一章 总则", "第二章 资质要求", "第三章 价格说明", "第四章 附件"]
    chunks_a = [make_heading(f"a_{i}", t) for i, t in enumerate(titles_a)]
    chunks_b = [make_heading(f"b_{i}", t, "doc_b") for i, t in enumerate(titles_b)]
    result = comparator.compare(chunks_a, chunks_b)
    assert result.title_jaccard == pytest.approx(0.333, abs=0.05)
    assert len(result.matched_sections) >= 2


def test_heading_marker_stripped(comparator):
    """§H§ 前缀应被正确去除"""
    chunks_a = [make_heading("a_0", "第一章 总则")]
    chunks_b = [make_heading("b_0", "第一章 总则", "doc_b")]
    result = comparator.compare(chunks_a, chunks_b)
    assert result.title_jaccard == pytest.approx(1.0, abs=0.01)
    # 匹配对中不应含 §H§
    for pair in result.matched_sections:
        assert "§H§" not in pair[0]
        assert "§H§" not in pair[1]

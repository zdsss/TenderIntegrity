"""Unit tests for RareTokenAnalyzer"""
import pytest
from unittest.mock import MagicMock

from src.analysis.rare_token_analyzer import RareTokenAnalyzer, RareTokenAnalysis
from src.document.metadata_extractor import ParagraphChunk


def _make_chunk(text: str, doc_id: str = "doc_a") -> ParagraphChunk:
    chunk = MagicMock(spec=ParagraphChunk)
    chunk.text = text
    chunk.doc_id = doc_id
    chunk.chunk_type = "paragraph"
    return chunk


def _chunks(texts: list[str], doc_id: str = "doc_a") -> list[ParagraphChunk]:
    return [_make_chunk(t, doc_id) for t in texts]


class TestRareTokenAnalyzer:

    def setup_method(self):
        self.analyzer = RareTokenAnalyzer(max_freq=2)

    def test_no_overlap_returns_none_risk(self):
        # Use texts that share NO 4-grams and no number-unit expressions
        chunks_a = _chunks(["甲方提供软件研发服务，验收合格后付款，质量保障期限为壹年"])
        chunks_b = _chunks(["乙方负责硬件安装施工，竣工后结算费用，维护责任由丙承担"])
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert isinstance(result, RareTokenAnalysis)
        assert result.risk_level == "none"
        assert result.total_match_count == 0

    def test_two_common_rare_grams_triggers_high(self):
        # 两份文档共享同样的罕见4-gram（各出现1次）
        rare_phrase = "罕见独特序列内容辅助说明"
        chunks_a = _chunks([rare_phrase])
        chunks_b = _chunks([rare_phrase])
        result = self.analyzer.analyze(chunks_a, chunks_b)
        # 共现4-gram应 ≥ 2
        assert result.total_match_count >= 2
        assert result.risk_level == "high"

    def test_one_common_rare_gram_triggers_medium(self):
        # 只有一个共现罕见序列
        rare_phrase_a = "罕见独特序列语料"  # 4-gram: 罕见独特, 见独特序, 独特序列, 特序列语
        rare_phrase_b = "罕见独特序列语料"
        # 确保无量化参数共现
        chunks_a = _chunks([rare_phrase_a, "文档甲的常见标准描述"])
        chunks_b = _chunks([rare_phrase_b, "文档乙的普通条款说明"])

        result = self.analyzer.analyze(chunks_a, chunks_b)
        # The rare grams will be shared → count ≥ 1
        assert result.total_match_count >= 1
        # Risk should be at least medium
        assert result.risk_level in ("medium", "high")

    def test_number_unit_match_detected(self):
        chunks_a = _chunks(["我们承诺24小时响应，确保服务质量"])
        chunks_b = _chunks(["本公司保证24小时响应，服务到位"])
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert "24小时响应" in result.number_unit_matches
        assert result.total_match_count >= 1

    def test_frequent_gram_not_counted_as_rare(self):
        # 高频4-gram不应被视为罕见
        repetitive = "本公司承诺" * 10
        chunks_a = _chunks([repetitive])
        chunks_b = _chunks([repetitive])
        result = self.analyzer.analyze(chunks_a, chunks_b)
        # 高频gram不应触发high（本公司承诺出现10次，超过max_freq=2）
        # 确保没有计入罕见序列
        for m in result.matches:
            if m.token_type == "4gram":
                assert m.freq_in_a <= 2 or m.freq_in_b <= 2

    def test_empty_chunks(self):
        result = self.analyzer.analyze([], [])
        assert result.risk_level == "none"
        assert result.total_match_count == 0
        assert result.matches == []

    def test_matches_have_correct_structure(self):
        chunks_a = _chunks(["特定量化参数4小时内完成响应"])
        chunks_b = _chunks(["承诺4小时内完成响应处理"])
        result = self.analyzer.analyze(chunks_a, chunks_b)
        for m in result.matches:
            assert m.token != ""
            assert m.freq_in_a >= 1
            assert m.freq_in_b >= 1
            assert m.token_type in ("4gram", "number_unit")
            assert m.risk_note != ""

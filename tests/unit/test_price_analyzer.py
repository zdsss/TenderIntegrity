"""Unit tests for PriceAnalyzer"""
import pytest
from unittest.mock import MagicMock

from src.analysis.price_analyzer import PriceAnalyzer, PriceAnalysis
from src.document.metadata_extractor import ParagraphChunk


def _make_chunk(text: str, chunk_type: str = "price_param") -> ParagraphChunk:
    chunk = MagicMock(spec=ParagraphChunk)
    chunk.text = text
    chunk.chunk_type = chunk_type
    return chunk


class TestPriceAnalyzer:

    def setup_method(self):
        self.analyzer = PriceAnalyzer(high_threshold=0.01, medium_threshold=0.05)

    def test_no_prices_returns_none_risk(self):
        chunks_a = [_make_chunk("技术方案描述，无价格信息")]
        chunks_b = [_make_chunk("另一份文档技术描述")]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert isinstance(result, PriceAnalysis)
        assert result.risk_level == "none"
        assert result.total_a is None
        assert result.total_b is None

    def test_very_close_prices_trigger_high(self):
        # 两份报价相差 < 1%
        chunks_a = [_make_chunk("合计：¥1,000,000元")]
        chunks_b = [_make_chunk("合计：¥1,005,000元")]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert result.total_a == 1_000_000.0
        assert result.total_b == 1_005_000.0
        assert result.proximity_ratio is not None
        assert result.proximity_ratio <= 0.01
        assert result.risk_level == "high"
        assert result.is_price_coordinated is True

    def test_medium_proximity_triggers_medium(self):
        # 差距 2~5%
        chunks_a = [_make_chunk("总价：500000元")]
        chunks_b = [_make_chunk("总价：515000元")]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert result.proximity_ratio is not None
        # 15000/515000 ≈ 2.9%
        assert 0.01 < result.proximity_ratio <= 0.05
        assert result.risk_level == "medium"

    def test_far_apart_prices_no_risk(self):
        chunks_a = [_make_chunk("报价总额：200000元")]
        chunks_b = [_make_chunk("报价总额：350000元")]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert result.risk_level == "none"
        assert result.is_price_coordinated is False

    def test_wan_yuan_unit_conversion(self):
        # 万元单位转换
        chunks_a = [_make_chunk("合计：100万元")]
        chunks_b = [_make_chunk("合计：101万元")]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        assert result.total_a == 1_000_000.0
        assert result.total_b == 1_010_000.0
        assert result.proximity_ratio is not None
        # 10000/1010000 ≈ 0.99%
        assert result.proximity_ratio <= 0.01
        assert result.risk_level == "high"

    def test_total_keyword_detection(self):
        # 含"合计"的行应被优先识别为总价
        chunks_a = [
            _make_chunk("项目A：50000元", "table_row"),
            _make_chunk("项目B：80000元", "table_row"),
            _make_chunk("合计：130000元", "table_row"),
        ]
        chunks_b = [
            _make_chunk("合计：131000元", "table_row"),
        ]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        # 应取合计行
        assert result.total_a == 130_000.0
        assert result.total_b == 131_000.0

    def test_empty_chunks_no_error(self):
        result = self.analyzer.analyze([], [])
        assert result.risk_level == "none"
        assert result.total_a is None
        assert result.total_b is None

    def test_coordinated_evidence_populated_on_risk(self):
        chunks_a = [_make_chunk("投标总价：999000元")]
        chunks_b = [_make_chunk("投标总价：999500元")]
        result = self.analyzer.analyze(chunks_a, chunks_b)
        if result.risk_level in ("high", "medium"):
            assert len(result.coordinated_evidence) > 0

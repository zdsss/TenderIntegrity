"""WhitelistFilter 单元测试"""
import pytest
from src.analysis.whitelist_filter import WhitelistFilter
from src.document.metadata_extractor import ParagraphChunk


@pytest.fixture
def whitelist_filter():
    return WhitelistFilter()  # 使用默认白名单目录


def make_chunk(text):
    return ParagraphChunk(chunk_id="test", doc_id="doc_a", text=text)


def test_legal_ref_detected(whitelist_filter):
    text = "根据《中华人民共和国招标投标法》第二十七条规定，投标人应当按照招标文件的要求编制投标文件。"
    assert whitelist_filter.is_whitelisted_regex(text)


def test_standard_ref_detected(whitelist_filter):
    text = "产品须符合GB/T 19001-2016质量管理体系要求以及YY/T 0316-2016医疗器械标准。"
    assert whitelist_filter.is_whitelisted_regex(text)


def test_normal_text_not_whitelisted(whitelist_filter):
    text = "本设备采用先进的超声波成像技术，图像分辨率达到业内领先水平，可精确识别0.5mm的微小病变。"
    assert not whitelist_filter.is_whitelisted_regex(text)


def test_filter_chunks_marks_correctly(whitelist_filter):
    chunks = [
        make_chunk("根据《药品管理法》第十条的相关规定，供应商需提供相应资质文件。"),
        make_chunk("本设备采用业界领先的AI辅助诊断算法，准确率高达99.5%，远超同类产品。"),
        make_chunk("符合GB/T 19001质量管理体系标准，通过ISO 13485认证。"),
    ]
    result = whitelist_filter.filter_chunks(chunks)
    assert result[0].is_whitelisted  # 法规引用
    assert not result[1].is_whitelisted  # 技术描述，非白名单
    assert result[2].is_whitelisted  # 标准引用

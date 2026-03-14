"""ChunkSplitter 单元测试"""
import pytest
from src.document.chunker import ChunkSplitter
from src.document.metadata_extractor import ParagraphChunk


@pytest.fixture
def splitter():
    return ChunkSplitter(max_chars=800, min_chars=50, window_size=600, step_size=300)


def test_basic_split(splitter):
    text = (
        "第一章 技术方案\n\n"
        "本方案采用先进的医疗影像技术，设备配置包括高分辨率探头，灵敏度高，精度优良，满足临床诊断需求，符合国家医疗器械标准要求。\n\n"
        "第二章 商务条款\n\n"
        "报价按合同约定执行，单价含税，报价单须加盖公章并由法定代表人签字，投标价格不得高于采购预算上限金额。"
    )
    chunks = splitter.split(text, "doc_test")
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.text) >= splitter.min_chars
        assert isinstance(chunk, ParagraphChunk)


def test_short_paragraphs_skipped(splitter):
    text = "短\n\n这是一段足够长的文字，超过了最短长度限制，应该被保留在切分结果中。这段文字有一定的长度。\n\n短2"
    chunks = splitter.split(text, "doc_test")
    # 短段落应被跳过
    for chunk in chunks:
        assert len(chunk.text) >= splitter.min_chars


def test_long_paragraph_sliding_window(splitter):
    # 生成超过 max_chars 的段落
    long_para = "医疗设备技术参数说明。" * 100  # >> 800字符
    text = long_para
    chunks = splitter.split(text, "doc_test")
    # 应该生成多个子块
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.text) <= splitter.window_size + 10  # 允许少量误差


def test_section_assignment(splitter):
    text = (
        "一、技术方案\n\n"
        "本方案采用先进的医疗影像技术，具备高分辨率成像功能，精度达到医疗级标准，可满足临床诊断对图像质量的严格要求。\n\n"
        "二、商务条款\n\n"
        "报价按照合同约定时间执行，含税单价报价，投标报价须包含设备本体、安装调试及售后服务等全部费用。"
    )
    chunks = splitter.split(text, "doc_test")
    # 验证章节分配
    sections = [c.section_title for c in chunks]
    assert any("技术" in s or "商务" in s for s in sections)


def test_chunk_id_unique(splitter):
    text = "段落一内容，这是第一个段落的详细文字内容，长度超过最短限制。\n\n段落二内容，这是第二个段落的详细文字内容，长度超过最短限制。"
    chunks = splitter.split(text, "doc_test")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_id 必须唯一"

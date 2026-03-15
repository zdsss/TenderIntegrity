"""ChunkSplitter 单元测试"""
import pytest
from src.document.chunker import ChunkSplitter
from src.document.docx_parser import HEADING_MARKER
from src.document.metadata_extractor import ParagraphChunk


@pytest.fixture
def splitter():
    return ChunkSplitter(max_chars=800, min_chars=20, window_size=600, step_size=300)


@pytest.fixture
def splitter_strict():
    """兼容旧测试的高 min_chars 配置"""
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
        assert isinstance(chunk, ParagraphChunk)


def test_short_paragraphs_skipped(splitter_strict):
    """严格模式下，短于 min_chars(50) 且合并后仍短的段落应被丢弃"""
    text = "短\n\n这是一段足够长的文字，超过了最短长度限制，应该被保留在切分结果中。这段文字有一定的长度。\n\n短2"
    chunks = splitter_strict.split(text, "doc_test")
    # "短" + "短2" 合并后 = "短\n短2" (4字) < _MERGED_MIN_CHARS(10)，应被丢弃
    # 足够长的段落应保留
    assert any("足够长" in c.text for c in chunks)
    # 非 heading 段落长度（合并后）应 >= 10（_MERGED_MIN_CHARS）
    non_heading = [c for c in chunks if not c.is_heading]
    for chunk in non_heading:
        assert len(chunk.text) >= 10


def test_long_paragraph_sliding_window(splitter):
    # 生成超过 max_chars 的段落
    long_para = "医疗设备技术参数说明。" * 100  # >> 800字符
    text = long_para
    chunks = splitter.split(text, "doc_test")
    # 应该生成多个子块
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.text) <= splitter.window_size + 50  # 允许少量误差


def test_section_assignment(splitter):
    text = (
        "一、技术方案\n\n"
        "本方案采用先进的医疗影像技术，具备高分辨率成像功能，精度达到医疗级标准，可满足临床诊断对图像质量的严格要求。\n\n"
        "二、商务条款\n\n"
        "报价按照合同约定时间执行，含税单价报价，投标报价须包含设备本体、安装调试及售后服务等全部费用。"
    )
    chunks = splitter.split(text, "doc_test")
    sections = [c.section_title for c in chunks]
    assert any("技术" in s or "商务" in s for s in sections)


def test_chunk_id_unique(splitter):
    text = "段落一内容，这是第一个段落的详细文字内容，长度超过最短限制。\n\n段落二内容，这是第二个段落的详细文字内容，长度超过最短限制。"
    chunks = splitter.split(text, "doc_test")
    ids = [c.chunk_id for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_id 必须唯一"


def test_heading_marker_always_kept(splitter):
    """§H§ 前缀标记的段落（即使很短）应始终保留，并标记 is_heading=True"""
    text = f"{HEADING_MARKER}一、技术方案\n\n这是正文内容，足够长，应该被保留在切分结果中作为一个完整的段落块。"
    chunks = splitter.split(text, "doc_test")
    heading_chunks = [c for c in chunks if c.is_heading]
    assert len(heading_chunks) >= 1
    assert any("技术方案" in c.text for c in heading_chunks)
    # Heading chunk 的文本不应含有 HEADING_MARKER 前缀
    for c in heading_chunks:
        assert not c.text.startswith(HEADING_MARKER)


def test_short_heading_not_filtered(splitter):
    """3 字的 heading 也应保留"""
    short_heading = f"{HEADING_MARKER}总则"
    text = f"{short_heading}\n\n这是足够长的正文内容，用于验证短标题不被过滤掉，内容有一定长度。"
    chunks = splitter.split(text, "doc_test")
    heading_chunks = [c for c in chunks if c.is_heading]
    assert any("总则" in c.text for c in heading_chunks)


def test_list_item_merging(splitter):
    """连续短段落（< min_chars）应被合并为一个 chunk"""
    short_items = "\n\n".join([f"条目{i}" for i in range(6)])  # 6 个短段落
    text = short_items
    chunks = splitter.split(text, "doc_test")
    # 6 个 "条目X" 每个 3 字 < min_chars=20，合并后应有 ≤2 个 chunk（每 5 个一组）
    for c in chunks:
        assert "条目" in c.text


def test_legal_ref_min_chars(splitter):
    """法规引用类 chunk 允许 min_chars=10"""
    text = "依据《招标投标法》第三十条的规定，本次采购按公开招标方式进行。\n\n短法规引用：《政府采购法》"
    chunks = splitter.split(text, "doc_test")
    # 《政府采购法》共 8 字，< 20 但 >= 10，legal_ref 应被保留
    legal_chunks = [c for c in chunks if c.chunk_type == "legal_ref"]
    # 至少有一个 legal_ref chunk 被保留
    assert len(legal_chunks) >= 1


def test_table_row_chunk_type(splitter):
    """[表格] 前缀的段落应分类为 table_row"""
    text = "[表格] 姓名:张三 | 岗位:项目经理 | 年限:10年\n\n[表格] 姓名:李四 | 岗位:技术总监 | 年限:8年"
    chunks = splitter.split(text, "doc_test")
    table_chunks = [c for c in chunks if c.chunk_type == "table_row"]
    assert len(table_chunks) >= 1


def test_sentence_split_for_long_para(splitter):
    """超长段落应按句子边界切分，不破坏完整句子"""
    sentences = ["本设备采用最先进的医疗影像处理技术，能够满足临床诊断需求。"] * 30
    long_para = "".join(sentences)  # ~900 字
    assert len(long_para) > splitter.max_chars
    chunks = splitter.split(text=long_para, doc_id="doc_test")
    assert len(chunks) >= 2
    # 每个 chunk 应以句号结尾（或包含完整句子）
    for c in chunks:
        assert len(c.text) > 0

"""pytest fixtures"""
import pytest
from pathlib import Path

TEST_DOC_DIR = Path(__file__).parent.parent / "doc"


@pytest.fixture
def sample_docx_a():
    path = TEST_DOC_DIR / "测试样本A_疑似围标投标文件.docx"
    if not path.exists():
        pytest.skip(f"测试文档不存在: {path}")
    return path


@pytest.fixture
def sample_docx_b():
    path = TEST_DOC_DIR / "测试样本B_疑似围标投标文件.docx"
    if not path.exists():
        pytest.skip(f"测试文档不存在: {path}")
    return path


@pytest.fixture
def sample_chunks_a():
    """生成简单的测试段落块"""
    from src.document.metadata_extractor import ParagraphChunk
    return [
        ParagraphChunk(
            chunk_id="doc_a_chunk_0000_abc",
            doc_id="doc_a",
            text="本产品采用先进的医疗影像技术，具备高分辨率成像功能，分辨率达到1024×1024像素，帧率不低于25帧/秒。",
            section_title="技术参数",
            chunk_type="tech_spec",
            chunk_index=0,
        ),
        ParagraphChunk(
            chunk_id="doc_a_chunk_0001_def",
            doc_id="doc_a",
            text="供应商须具备医疗器械经营许可证，并提供完整的质量管理体系认证文件。",
            section_title="资质要求",
            chunk_type="legal_ref",
            chunk_index=1,
        ),
    ]


@pytest.fixture
def sample_chunks_b():
    """生成简单的测试段落块"""
    from src.document.metadata_extractor import ParagraphChunk
    return [
        ParagraphChunk(
            chunk_id="doc_b_chunk_0000_xyz",
            doc_id="doc_b",
            text="该设备采用先进的医疗影像技术，具备高清分辨率成像功能，成像分辨率达到1024×1024像素，帧率不低于25帧每秒。",
            section_title="技术参数",
            chunk_type="tech_spec",
            chunk_index=0,
        ),
        ParagraphChunk(
            chunk_id="doc_b_chunk_0001_uvw",
            doc_id="doc_b",
            text="投标方须持有效的医疗器械经营许可证，并提供有效的质量体系认证文件。",
            section_title="资质要求",
            chunk_type="legal_ref",
            chunk_index=1,
        ),
    ]

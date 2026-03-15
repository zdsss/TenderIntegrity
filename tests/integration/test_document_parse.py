"""文档解析集成测试"""
import pytest
from pathlib import Path
from src.document.parser import DocumentParser


@pytest.fixture
def parser():
    return DocumentParser()


def test_docx_parse(sample_docx_a, parser):
    chunks = parser.parse_to_chunks(sample_docx_a, "doc_a")
    assert len(chunks) > 0
    for chunk in chunks:
        assert len(chunk.text) >= 10
        assert chunk.doc_id == "doc_a"
        assert chunk.chunk_id


def test_docx_text_parse(sample_docx_a, parser):
    text = parser.parse_to_text(sample_docx_a)
    assert len(text) > 100


def test_chunk_metadata(sample_docx_a, parser):
    chunks = parser.parse_to_chunks(sample_docx_a, "doc_a")
    assert all(c.chunk_type in {"legal_ref", "standard_ref", "price_param", "tech_spec", "normal", "table_row", "table_header"} for c in chunks)
    assert all(c.chunk_index >= 0 for c in chunks)


def test_unsupported_format(tmp_path, parser):
    fake_file = tmp_path / "test.xlsx"
    fake_file.write_bytes(b"fake content")
    with pytest.raises(ValueError, match="不支持的文件类型"):
        parser.parse_to_chunks(fake_file, "doc_test")

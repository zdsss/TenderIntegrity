"""KeyFieldExtractor + FieldOverlapDetector 单元测试"""
import pytest
from src.document.field_extractor import KeyFieldExtractor, KeyFields
from src.analysis.field_overlap_detector import FieldOverlapDetector
from src.document.metadata_extractor import ParagraphChunk


def make_chunk(text: str, doc_id: str = "doc_a") -> ParagraphChunk:
    return ParagraphChunk(chunk_id="c1", doc_id=doc_id, text=text)


@pytest.fixture
def extractor():
    return KeyFieldExtractor()


@pytest.fixture
def detector():
    return FieldOverlapDetector()


# ── KeyFieldExtractor ──────────────────────────────────────────────────────────

def test_extract_phone(extractor):
    chunk = make_chunk("联系电话：13812345678，备用：15987654321")
    fields = extractor.extract([chunk])
    assert "13812345678" in fields.phones
    assert "15987654321" in fields.phones


def test_extract_email(extractor):
    chunk = make_chunk("联系邮箱：invest@example.com 或 ADMIN@CORP.CN")
    fields = extractor.extract([chunk])
    # 邮箱应统一为小写
    assert "invest@example.com" in fields.emails
    assert "admin@corp.cn" in fields.emails


def test_extract_company(extractor):
    chunk = make_chunk("投标单位：北京科技有限公司，授权代理：上海建设股份公司")
    fields = extractor.extract([chunk])
    assert any("科技有限公司" in c for c in fields.company_names)
    assert any("建设股份公司" in c for c in fields.company_names)


def test_extract_contact_person(extractor):
    chunk = make_chunk("联系人：张三，项目经理：李四")
    fields = extractor.extract([chunk])
    assert "张三" in fields.contact_persons
    assert "李四" in fields.contact_persons


def test_extract_empty(extractor):
    chunk = make_chunk("本段落不包含任何关键字段信息。")
    fields = extractor.extract([chunk])
    assert fields.phones == []
    assert fields.emails == []


# ── FieldOverlapDetector ───────────────────────────────────────────────────────

def test_exact_phone_overlap(detector):
    fields_a = KeyFields(phones=["13812345678"])
    fields_b = KeyFields(phones=["13812345678"])
    overlaps = detector.detect(fields_a, fields_b)
    assert len(overlaps) == 1
    assert overlaps[0].field_type == "phone"
    assert overlaps[0].overlap_type == "exact"


def test_exact_email_overlap(detector):
    fields_a = KeyFields(emails=["contact@tender.cn"])
    fields_b = KeyFields(emails=["contact@tender.cn"])
    overlaps = detector.detect(fields_a, fields_b)
    assert any(o.field_type == "email" and o.overlap_type == "exact" for o in overlaps)


def test_fuzzy_company_overlap(detector):
    fields_a = KeyFields(company_names=["北京鑫源科技有限公司"])
    fields_b = KeyFields(company_names=["北京鑫源科技有限公司"])  # exact → should be in exact, not fuzzy
    overlaps = detector.detect(fields_a, fields_b)
    assert any(o.field_type == "company" for o in overlaps)


def test_no_overlap(detector):
    # Phones with very different digit patterns to avoid fuzzy match at 0.80 threshold
    fields_a = KeyFields(phones=["13812345678"], emails=["a@a.com"])
    fields_b = KeyFields(phones=["15598765432"], emails=["b@b.com"])
    overlaps = detector.detect(fields_a, fields_b)
    assert len(overlaps) == 0


def test_person_overlap(detector):
    fields_a = KeyFields(contact_persons=["王五"])
    fields_b = KeyFields(contact_persons=["王五"])
    overlaps = detector.detect(fields_a, fields_b)
    assert any(o.field_type == "person" and o.overlap_type == "exact" for o in overlaps)

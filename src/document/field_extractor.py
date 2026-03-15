"""关键字段提取：公司名、联系人、电话、邮箱、项目名"""
import re
import logging
from dataclasses import dataclass, field

from src.document.metadata_extractor import ParagraphChunk

logger = logging.getLogger(__name__)

# 正则模式
_PHONE_RE = re.compile(r"1[3-9]\d{9}")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_COMPANY_RE = re.compile(r"[\u4e00-\u9fa5A-Za-z0-9（）()·\-]{2,20}(?:有限公司|股份公司|有限责任公司|集团公司|科技公司|工程公司|建设公司)")
_PROJECT_RE = re.compile(r"[\u4e00-\u9fa5A-Za-z0-9（）()·\-]{4,40}(?:项目|工程|采购|招标)")

# 联系人上下文关键词（在这些词附近的中文人名视为联系人）
_CONTACT_KEYWORDS = re.compile(r"联系人[：:]\s*([\u4e00-\u9fa5]{2,4})")
_MANAGER_KEYWORDS = re.compile(r"(?:项目经理|负责人|联系人)[：:]\s*([\u4e00-\u9fa5]{2,4})")


@dataclass
class KeyFields:
    company_names: list[str] = field(default_factory=list)
    contact_persons: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    emails: list[str] = field(default_factory=list)
    project_names: list[str] = field(default_factory=list)


class KeyFieldExtractor:
    """从 ParagraphChunk 列表中提取关键字段"""

    def extract(self, chunks: list[ParagraphChunk]) -> KeyFields:
        company_names: set[str] = set()
        contact_persons: set[str] = set()
        phones: set[str] = set()
        emails: set[str] = set()
        project_names: set[str] = set()

        for chunk in chunks:
            text = chunk.text

            phones.update(_PHONE_RE.findall(text))
            emails.update(m.lower() for m in _EMAIL_RE.findall(text))
            company_names.update(_COMPANY_RE.findall(text))
            project_names.update(_PROJECT_RE.findall(text))

            for m in _CONTACT_KEYWORDS.finditer(text):
                contact_persons.add(m.group(1))
            for m in _MANAGER_KEYWORDS.finditer(text):
                contact_persons.add(m.group(1))

        result = KeyFields(
            company_names=sorted(company_names),
            contact_persons=sorted(contact_persons),
            phones=sorted(phones),
            emails=sorted(emails),
            project_names=sorted(project_names),
        )
        logger.debug(
            f"字段提取: 公司={len(result.company_names)}, 联系人={len(result.contact_persons)}, "
            f"电话={len(result.phones)}, 邮箱={len(result.emails)}, 项目={len(result.project_names)}"
        )
        return result

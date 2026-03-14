"""段落元数据提取：章节识别、段落类型分类"""
import re
from dataclasses import dataclass, field
from typing import Literal

ChunkType = Literal["legal_ref", "standard_ref", "price_param", "tech_spec", "normal"]

# 章节标题正则（多种中文标书格式）
SECTION_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百千\d]+[章节条款]\s*[：:]?\s*(.+)$"),
    re.compile(r"^[一二三四五六七八九十]+[、.．]\s*(.+)$"),
    re.compile(r"^(\d+)\.\s*(.+)$"),
    re.compile(r"^(\d+\.\d+)\s+(.+)$"),
    re.compile(r"^[\(（]\s*[一二三四五六七八九十\d]+\s*[\)）]\s*(.+)$"),
]

# 法规引用正则
LEGAL_REF_PATTERNS = [
    re.compile(r"《[^》]{2,30}法》"),
    re.compile(r"《[^》]{2,30}条例》"),
    re.compile(r"《[^》]{2,30}规定》"),
    re.compile(r"《[^》]{2,30}办法》"),
    re.compile(r"第[一二三四五六七八九十百\d]+条[^\w]"),
]

# 标准引用正则
STANDARD_REF_PATTERNS = [
    re.compile(r"GB/T\s*\d{4,6}"),
    re.compile(r"GB\s*\d{4,6}"),
    re.compile(r"YY/T\s*\d{4,6}"),
    re.compile(r"YY\s*\d{4,6}"),
    re.compile(r"ISO\s*\d{4,6}"),
    re.compile(r"ISO/IEC\s*\d{4,6}"),
    re.compile(r"IEC\s*\d{4,6}"),
    re.compile(r"WS/T\s*\d{4,6}"),
]

# 价格参数关键词
PRICE_KEYWORDS = [
    "报价", "单价", "总价", "含税价", "不含税", "预算", "投标价",
    "元/", "万元", "RMB", "人民币", "报价单", "价格表",
]

# 技术规格关键词
TECH_SPEC_KEYWORDS = [
    "技术参数", "技术规格", "技术要求", "性能指标", "配置要求",
    "功能要求", "精度", "分辨率", "灵敏度", "量程", "通道",
    "频率", "功率", "电压", "电流", "接口", "协议", "兼容",
]


@dataclass
class ParagraphChunk:
    """段落块数据模型"""
    chunk_id: str
    doc_id: str
    text: str
    page_num: int = 0
    section_title: str = ""
    chunk_type: ChunkType = "normal"
    is_whitelisted: bool = False
    chunk_index: int = 0
    char_count: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        self.char_count = len(self.text)


class MetadataExtractor:
    """章节标题识别和段落类型分类"""

    def extract_section_title(self, text: str) -> str | None:
        """判断文本是否为章节标题，返回标题文本或 None"""
        text = text.strip()
        if len(text) > 100:
            return None
        for pattern in SECTION_PATTERNS:
            m = pattern.match(text)
            if m:
                return text
        return None

    def classify_chunk_type(self, text: str) -> ChunkType:
        """分类段落类型"""
        # 法规引用
        for pattern in LEGAL_REF_PATTERNS:
            if pattern.search(text):
                return "legal_ref"

        # 标准引用
        for pattern in STANDARD_REF_PATTERNS:
            if pattern.search(text):
                return "standard_ref"

        # 价格参数
        price_hits = sum(1 for kw in PRICE_KEYWORDS if kw in text)
        if price_hits >= 2:
            return "price_param"

        # 技术规格
        tech_hits = sum(1 for kw in TECH_SPEC_KEYWORDS if kw in text)
        if tech_hits >= 2:
            return "tech_spec"

        return "normal"

    def assign_sections(self, raw_paragraphs: list[str]) -> list[tuple[str, str]]:
        """
        为每个段落分配所属章节标题
        Returns: list of (paragraph_text, section_title)
        """
        result = []
        current_section = ""
        for para in raw_paragraphs:
            title = self.extract_section_title(para)
            if title:
                current_section = title
            result.append((para, current_section))
        return result

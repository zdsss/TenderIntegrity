"""罕见字符序列共现检测器 (Q1)

检测两份文档中共同出现的罕见汉字4-gram序列，以及精确数字量化参数复用。
罕见序列定义：在单份文档中出现 ≤ 2 次的4-gram（非模板短语）。
"""
import re
import logging
from collections import Counter
from dataclasses import dataclass, field

from src.document.metadata_extractor import ParagraphChunk

logger = logging.getLogger(__name__)

# 数字+单位组合（如 4小时响应、600家供应商、24小时解决）
_NUMBER_UNIT_RE = re.compile(
    r"\d+(?:\.\d+)?\s*(?:小时|分钟|天|日|年|月|家|个|项|套|台|件|次|人|%|％|万|亿|千|百)"
    r"(?:响应|解决|处理|维修|上门|供应商|合作|服务|案例|经验|保障|运维|测试|支持)?"
)

# 停用4-gram（常见模板短语，不计入罕见序列）
_STOP_4GRAMS = {
    "本公司承诺", "严格按照", "相关法律法", "法律法规的", "律法规的规", "规的规定执",
    "的规定执行", "符合招标文", "招标文件要", "文件要求的", "我公司将严", "公司将严格",
    "将严格按照", "提供优质的", "优质的服务", "质量保证期", "量保证期内", "保证期内免",
    "证期内免费", "期内免费维", "内免费维修", "免费维修更", "费维修更换",
    "的技术支持", "技术支持和", "本次投标的", "次投标的产",
}


def _extract_4grams(text: str) -> list[str]:
    """提取文本中所有连续汉字4-gram"""
    # 只保留汉字段
    chinese_segments = re.findall(r'[\u4e00-\u9fa5]{4,}', text)
    grams = []
    for seg in chinese_segments:
        for i in range(len(seg) - 3):
            gram = seg[i:i+4]
            if gram not in _STOP_4GRAMS:
                grams.append(gram)
    return grams


def _extract_number_units(text: str) -> list[str]:
    """提取文本中的数字+单位量化表达式"""
    return _NUMBER_UNIT_RE.findall(text)


@dataclass
class RareTokenMatch:
    token: str           # 匹配的罕见字符序列
    freq_in_a: int       # 在文档A中出现次数
    freq_in_b: int       # 在文档B中出现次数
    token_type: str      # "4gram" / "number_unit"
    risk_note: str


@dataclass
class RareTokenAnalysis:
    matches: list[RareTokenMatch] = field(default_factory=list)
    risk_level: str = "none"       # "high" / "medium" / "none"
    total_match_count: int = 0
    number_unit_matches: list[str] = field(default_factory=list)


class RareTokenAnalyzer:
    """检测两份文档间罕见字符序列和量化参数的共现"""

    def __init__(self, max_freq: int = 2):
        """
        Args:
            max_freq: 认定为"罕见"的最大出现次数（在单份文档内）
        """
        self.max_freq = max_freq

    def _get_rare_grams(self, text: str) -> set[str]:
        """返回文本中出现频率 <= max_freq 的4-gram集合"""
        counter = Counter(_extract_4grams(text))
        return {gram for gram, cnt in counter.items() if cnt <= self.max_freq}

    def _get_all_number_units(self, text: str) -> set[str]:
        """返回文本中所有数字+单位量化表达式"""
        return set(_extract_number_units(text))

    def analyze(
        self,
        chunks_a: list[ParagraphChunk],
        chunks_b: list[ParagraphChunk],
    ) -> RareTokenAnalysis:
        """分析两份文档的罕见序列共现情况"""
        text_a = "\n".join(c.text for c in chunks_a)
        text_b = "\n".join(c.text for c in chunks_b)

        # 4-gram 频率计数（用于记录出现次数）
        counter_a = Counter(_extract_4grams(text_a))
        counter_b = Counter(_extract_4grams(text_b))

        # 罕见4-gram集合（各自文档内稀少的）
        rare_a = {g for g, cnt in counter_a.items() if cnt <= self.max_freq}
        rare_b = {g for g, cnt in counter_b.items() if cnt <= self.max_freq}
        common_rare = rare_a & rare_b

        # 数字+单位量化参数
        num_units_a = self._get_all_number_units(text_a)
        num_units_b = self._get_all_number_units(text_b)
        common_num_units = num_units_a & num_units_b

        matches: list[RareTokenMatch] = []

        for gram in sorted(common_rare):
            matches.append(RareTokenMatch(
                token=gram,
                freq_in_a=counter_a[gram],
                freq_in_b=counter_b[gram],
                token_type="4gram",
                risk_note=f"罕见汉字序列「{gram}」在两份文档中均出现（A:{counter_a[gram]}次, B:{counter_b[gram]}次）",
            ))

        for nu in sorted(common_num_units):
            matches.append(RareTokenMatch(
                token=nu,
                freq_in_a=sum(1 for m in _extract_number_units(text_a) if m == nu),
                freq_in_b=sum(1 for m in _extract_number_units(text_b) if m == nu),
                token_type="number_unit",
                risk_note=f"量化参数「{nu}」在两份文档中完全相同",
            ))

        total_match_count = len(common_rare) + len(common_num_units)

        if total_match_count >= 2:
            risk_level = "high"
        elif total_match_count == 1:
            risk_level = "medium"
        else:
            risk_level = "none"

        result = RareTokenAnalysis(
            matches=matches,
            risk_level=risk_level,
            total_match_count=total_match_count,
            number_unit_matches=sorted(common_num_units),
        )

        logger.info(
            f"罕见序列分析: 4gram共现={len(common_rare)}, 量化参数共现={len(common_num_units)}, "
            f"风险={risk_level}"
        )
        return result

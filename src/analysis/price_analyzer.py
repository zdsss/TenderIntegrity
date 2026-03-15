"""价格异常分析器 (Q2)

从文档块中提取货币金额，检测两份文档报价是否存在协同定价迹象。
"""
import re
import logging
from dataclasses import dataclass, field

from src.document.metadata_extractor import ParagraphChunk

logger = logging.getLogger(__name__)

# 货币金额正则：支持 ¥、￥、人民币 前缀，支持逗号分隔和无分隔的大数字，支持万元/亿元后缀
_PRICE_RE = re.compile(
    r"(?:[¥￥]|人民币)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(万元|亿元|元|元整)?",
    re.IGNORECASE,
)

# 合计/总价关键词
_TOTAL_KEYWORDS = re.compile(r"合计|总价|报价总额|投标总价|总报价|总金额|含税总价")

# 最小有效金额（过滤掉数量、编号等小数字）
_MIN_AMOUNT = 100.0


def _normalize_amount(value_str: str, unit: str | None) -> float:
    """将金额字符串+单位转换为元"""
    amount = float(value_str.replace(",", ""))
    if unit == "万元":
        amount *= 10_000
    elif unit == "亿元":
        amount *= 100_000_000
    return amount


def _extract_amounts(text: str) -> list[tuple[float, str]]:
    """从文本中提取 (金额, 原始文本) 列表"""
    results = []
    for m in _PRICE_RE.finditer(text):
        raw = m.group(0).strip()
        try:
            amount = _normalize_amount(m.group(1), m.group(2))
            if amount >= _MIN_AMOUNT:
                results.append((amount, raw))
        except (ValueError, AttributeError):
            continue
    return results


@dataclass
class PriceItem:
    label: str       # 价格项名称（所在行的文字上下文）
    amount: float    # 金额（元）
    raw_text: str    # 原始匹配文本


@dataclass
class PriceAnalysis:
    prices_a: list[PriceItem] = field(default_factory=list)
    prices_b: list[PriceItem] = field(default_factory=list)
    total_a: float | None = None
    total_b: float | None = None
    proximity_ratio: float | None = None  # |A-B| / max(A,B)，越小越可疑
    is_price_coordinated: bool = False
    coordinated_evidence: list[str] = field(default_factory=list)
    risk_level: str = "none"              # "high" / "medium" / "none"


def _find_total(chunks: list[ParagraphChunk]) -> float | None:
    """尝试从块列表中找到合计/总价行，返回金额（元）"""
    candidates: list[float] = []
    for chunk in chunks:
        text = chunk.text
        if _TOTAL_KEYWORDS.search(text):
            amounts = _extract_amounts(text)
            if amounts:
                # 取行内最大金额
                candidates.append(max(a for a, _ in amounts))
    if candidates:
        return max(candidates)
    return None


def _collect_price_items(chunks: list[ParagraphChunk]) -> list[PriceItem]:
    """从 price_param / table_row 类型块中提取所有价格项"""
    items: list[PriceItem] = []
    target_types = {"price_param", "table_row", "table_header"}
    for chunk in chunks:
        if chunk.chunk_type not in target_types:
            continue
        text = chunk.text
        for amount, raw in _extract_amounts(text):
            # 用文本前40字符作为标签
            label = text[:40].strip()
            items.append(PriceItem(label=label, amount=amount, raw_text=raw))
    return items


class PriceAnalyzer:
    """检测两份文档报价的协同定价迹象"""

    def __init__(
        self,
        high_threshold: float = 0.01,   # proximity_ratio ≤ 1% → high
        medium_threshold: float = 0.05, # proximity_ratio ≤ 5% → medium
    ):
        self.high_threshold = high_threshold
        self.medium_threshold = medium_threshold

    def analyze(
        self,
        chunks_a: list[ParagraphChunk],
        chunks_b: list[ParagraphChunk],
    ) -> PriceAnalysis:
        """分析两份文档价格接近度"""
        prices_a = _collect_price_items(chunks_a)
        prices_b = _collect_price_items(chunks_b)

        # 优先使用合计/总价行
        total_a = _find_total(chunks_a)
        total_b = _find_total(chunks_b)

        # 若无明确合计行，取所有价格中最大值
        if total_a is None and prices_a:
            total_a = max(item.amount for item in prices_a)
        if total_b is None and prices_b:
            total_b = max(item.amount for item in prices_b)

        result = PriceAnalysis(prices_a=prices_a, prices_b=prices_b, total_a=total_a, total_b=total_b)

        if total_a is None or total_b is None or total_a == 0 or total_b == 0:
            logger.info("价格分析: 未提取到有效合计金额，跳过接近度计算")
            return result

        proximity = abs(total_a - total_b) / max(total_a, total_b)
        result.proximity_ratio = proximity

        evidence: list[str] = []
        if proximity <= self.high_threshold:
            result.risk_level = "high"
            result.is_price_coordinated = True
            evidence.append(
                f"两份文档总报价接近度 {proximity:.2%}（A={total_a:,.0f}元, B={total_b:,.0f}元），"
                f"差距 ≤1%，疑似协同定价"
            )
        elif proximity <= self.medium_threshold:
            result.risk_level = "medium"
            result.is_price_coordinated = True
            evidence.append(
                f"两份文档总报价接近度 {proximity:.2%}（A={total_a:,.0f}元, B={total_b:,.0f}元），"
                f"差距 ≤5%，存在协同定价风险"
            )
        else:
            result.risk_level = "none"

        result.coordinated_evidence = evidence

        logger.info(
            f"价格分析: total_a={total_a}, total_b={total_b}, "
            f"proximity={proximity:.2%}, risk={result.risk_level}"
        )
        return result

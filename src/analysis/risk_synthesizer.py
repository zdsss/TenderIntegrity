"""综合风险合成器 (Q5)

整合文本相似度、结构分析、字段重叠、罕见序列、价格分析、元数据对比，
输出最终风险等级，修复"纯文本分低但其他强信号"的漏判问题。
"""
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class CompositeRisk:
    final_level: str           # "high" / "medium" / "low"
    text_risk_level: str       # 来自 compute_overall_risk
    text_similarity_rate: float
    triggered_signals: list[str] = field(default_factory=list)  # 触发的高风险信号描述
    signal_breakdown: dict = field(default_factory=dict)         # 各维度贡献


class RiskSynthesizer:
    """整合多维度信号，输出综合风险等级"""

    def synthesize(
        self,
        text_level: str,
        text_rate: float,
        structure: dict | None,
        field_overlaps: list[dict],
        rare_token: dict | None,
        price: dict | None,
        meta: dict | None,
    ) -> CompositeRisk:
        """
        合成规则（任一触发即升级）：
        - 电话/邮箱精确重叠 → HIGH
        - 团队成员精确重叠 ≥ 1 → HIGH
        - 罕见序列匹配 ≥ 2 → HIGH
        - 价格接近度 ≤ 1% → HIGH
        - 文档元数据同作者/同公司 → HIGH
        - 结构分 ≥ 70 + 文本率 ≥ 30% → HIGH
        - 结构分 ≥ 50 + 字段模糊重叠 ≥ 1 → MEDIUM↑
        - 时间戳聚集（≤30分钟）+ 文本率 ≥ 15% → MEDIUM↑
        - 价格接近度 ≤ 5% → MEDIUM↑
        """
        signals: list[str] = []
        breakdown: dict = {
            "text": text_level,
            "structure": None,
            "field_overlaps": [],
            "rare_token": None,
            "price": None,
            "meta": None,
        }

        forced_high = False
        forced_medium = False

        # ── 字段重叠检测 ──────────────────────────────────────────────────
        exact_phone_emails = [
            o for o in field_overlaps
            if o.get("overlap_type") == "exact" and o.get("field_type") in ("phone", "email")
        ]
        exact_team_members = [
            o for o in field_overlaps
            if o.get("overlap_type") == "exact" and o.get("field_type") in ("person", "team_member")
        ]
        fuzzy_overlaps = [
            o for o in field_overlaps
            if o.get("overlap_type") == "fuzzy"
        ]

        breakdown["field_overlaps"] = {
            "exact_phone_email_count": len(exact_phone_emails),
            "exact_team_member_count": len(exact_team_members),
            "fuzzy_count": len(fuzzy_overlaps),
        }

        if exact_phone_emails:
            forced_high = True
            for o in exact_phone_emails:
                signals.append(
                    f"电话/邮箱精确重叠: {o.get('field_type')} = {o.get('value_a')!r}"
                )

        if exact_team_members:
            forced_high = True
            for o in exact_team_members:
                signals.append(
                    f"团队成员精确重叠: {o.get('value_a')!r}"
                )

        # ── 罕见序列 ──────────────────────────────────────────────────────
        if rare_token:
            rt_level = rare_token.get("risk_level", "none")
            rt_count = rare_token.get("total_match_count", 0)
            breakdown["rare_token"] = {"risk_level": rt_level, "total_match_count": rt_count}
            if rt_count >= 2:
                forced_high = True
                signals.append(f"罕见序列匹配 {rt_count} 项（含低频汉字4-gram和量化参数复用）")
            elif rt_count == 1:
                forced_medium = True
                signals.append("罕见序列匹配 1 项（低频汉字4-gram或量化参数复用）")

        # ── 价格分析 ──────────────────────────────────────────────────────
        if price:
            price_level = price.get("risk_level", "none")
            proximity = price.get("proximity_ratio")
            breakdown["price"] = {"risk_level": price_level, "proximity_ratio": proximity}
            if price_level == "high":
                forced_high = True
                signals.append(
                    f"报价接近度 {proximity:.2%} ≤1%，疑似协同定价"
                    if proximity is not None else "报价高风险"
                )
            elif price_level == "medium":
                forced_medium = True
                signals.append(
                    f"报价接近度 {proximity:.2%} ≤5%，存在协同定价风险"
                    if proximity is not None else "报价中等风险"
                )

        # ── 元数据对比 ──────────────────────────────────────────────────────
        if meta:
            meta_level = meta.get("risk_level", "none")
            breakdown["meta"] = {"risk_level": meta_level}
            if meta_level == "high":
                forced_high = True
                for note in meta.get("risk_notes", []):
                    signals.append(f"文档元数据: {note}")
            elif meta_level == "medium":
                time_gap = meta.get("time_gap_minutes")
                is_clustered = meta.get("is_timestamp_clustered", False)
                if is_clustered and text_rate >= 0.15:
                    forced_medium = True
                    signals.append(
                        f"时间戳聚集（{time_gap:.1f}分钟）+ 文本雷同率 {text_rate:.1%}"
                        if time_gap is not None else "时间戳聚集 + 文本雷同率 ≥15%"
                    )

        # ── 结构分析 ──────────────────────────────────────────────────────
        if structure:
            struct_score = structure.get("overall_score", 0)
            struct_level = structure.get("structure_risk_level", "none")
            breakdown["structure"] = {"score": struct_score, "risk_level": struct_level}
            if struct_score >= 70 and text_rate >= 0.30:
                forced_high = True
                signals.append(
                    f"结构分 {struct_score:.0f}/100 (≥70) + 文本雷同率 {text_rate:.1%} (≥30%)"
                )
            elif struct_score >= 50 and fuzzy_overlaps:
                forced_medium = True
                signals.append(
                    f"结构分 {struct_score:.0f}/100 (≥50) + 字段模糊重叠 {len(fuzzy_overlaps)} 项"
                )

        # ── 最终判定 ──────────────────────────────────────────────────────
        if forced_high:
            final_level = "high"
        elif forced_medium:
            # 中等信号：至少提升到 medium
            if text_level == "high":
                final_level = "high"
            else:
                final_level = "medium"
        else:
            # 无额外信号：沿用文本风险等级
            final_level = text_level if text_level in ("high", "medium", "low") else "low"

        result = CompositeRisk(
            final_level=final_level,
            text_risk_level=text_level,
            text_similarity_rate=text_rate,
            triggered_signals=signals,
            signal_breakdown=breakdown,
        )

        logger.info(
            f"综合风险合成: text={text_level}({text_rate:.1%}), "
            f"signals={len(signals)}, final={final_level}"
        )
        return result

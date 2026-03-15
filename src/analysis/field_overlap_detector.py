"""关键字段重叠检测：精确匹配 + 模糊匹配"""
import difflib
import logging
from dataclasses import dataclass

from src.document.field_extractor import KeyFields

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.80  # 模糊匹配最低相似度（Q4：从0.85降至0.80，捕获近似电话号码）


@dataclass
class FieldOverlap:
    field_type: str    # "phone" / "email" / "person" / "company" / "project" / "team_member"
    value_a: str
    value_b: str
    overlap_type: str  # "exact" / "fuzzy"
    risk_note: str


class FieldOverlapDetector:
    """检测两份文档关键字段的重叠情况"""

    def _exact_overlap(self, list_a: list[str], list_b: list[str], field_type: str, note_tmpl: str) -> list[FieldOverlap]:
        overlaps = []
        set_b = set(list_b)
        for val in list_a:
            if val in set_b:
                overlaps.append(FieldOverlap(
                    field_type=field_type,
                    value_a=val,
                    value_b=val,
                    overlap_type="exact",
                    risk_note=note_tmpl.format(val=val),
                ))
        return overlaps

    def _fuzzy_overlap(
        self,
        list_a: list[str],
        list_b: list[str],
        field_type: str,
        note_tmpl: str,
        threshold: float = FUZZY_THRESHOLD,
    ) -> list[FieldOverlap]:
        overlaps = []
        for val_a in list_a:
            for val_b in list_b:
                if val_a == val_b:
                    continue  # 已由精确匹配处理
                ratio = difflib.SequenceMatcher(None, val_a, val_b).ratio()
                if ratio >= threshold:
                    overlaps.append(FieldOverlap(
                        field_type=field_type,
                        value_a=val_a,
                        value_b=val_b,
                        overlap_type="fuzzy",
                        risk_note=note_tmpl.format(val=f"{val_a} ≈ {val_b}"),
                    ))
        return overlaps

    def detect(self, fields_a: KeyFields, fields_b: KeyFields) -> list[FieldOverlap]:
        """检测两份文档的字段重叠，返回所有重叠项"""
        overlaps: list[FieldOverlap] = []

        # 电话：精确匹配即为高风险
        overlaps.extend(self._exact_overlap(
            fields_a.phones, fields_b.phones, "phone",
            "两份文档出现相同联系电话 {val}，疑似同一投标主体"
        ))
        # 电话：模糊匹配（捕获仅末几位不同的近似号码）
        overlaps.extend(self._fuzzy_overlap(
            fields_a.phones, fields_b.phones, "phone",
            "两份文档联系电话高度相似 {val}，疑似关联主体"
        ))

        # 邮箱：精确匹配（不区分大小写已在提取时统一小写）
        overlaps.extend(self._exact_overlap(
            fields_a.emails, fields_b.emails, "email",
            "两份文档出现相同电子邮箱 {val}，疑似同一投标主体"
        ))

        # 联系人：精确 + 模糊
        overlaps.extend(self._exact_overlap(
            fields_a.contact_persons, fields_b.contact_persons, "person",
            "两份文档出现相同联系人 {val}"
        ))
        overlaps.extend(self._fuzzy_overlap(
            fields_a.contact_persons, fields_b.contact_persons, "person",
            "两份文档联系人高度相似 {val}"
        ))

        # 公司名：精确 + 模糊
        overlaps.extend(self._exact_overlap(
            fields_a.company_names, fields_b.company_names, "company",
            "两份文档出现相同公司名称 {val}"
        ))
        overlaps.extend(self._fuzzy_overlap(
            fields_a.company_names, fields_b.company_names, "company",
            "两份文档公司名称高度相似 {val}，疑似关联公司"
        ))

        # 团队成员：精确 + 模糊（Q4：新增）
        overlaps.extend(self._exact_overlap(
            fields_a.team_members, fields_b.team_members, "team_member",
            "两份文档出现相同团队成员 {val}，疑似人员交叉"
        ))
        overlaps.extend(self._fuzzy_overlap(
            fields_a.team_members, fields_b.team_members, "team_member",
            "两份文档团队成员高度相似 {val}"
        ))

        logger.info(f"字段重叠检测: {len(overlaps)} 项重叠")
        return overlaps

"""DOCX 文件元数据提取与对比 (Q3)

使用 python-docx core_properties 提取作者、修改时间等元数据，
检测两份文档是否存在时间戳聚集、同一作者等异常。
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class DocxMeta:
    author: str = ""
    last_modified_by: str = ""
    company: str = ""
    created: datetime | None = None
    modified: datetime | None = None
    revision: int = 0
    source_path: str = ""


@dataclass
class MetaComparison:
    same_author: bool = False
    same_last_modifier: bool = False
    same_company: bool = False
    time_gap_minutes: float | None = None   # 两文档修改时间差（分钟）
    is_timestamp_clustered: bool = False    # 时间差 ≤ 30 分钟
    risk_notes: list[str] = field(default_factory=list)
    risk_level: str = "none"               # "high" / "medium" / "none"


def extract_docx_meta(file_path: str) -> DocxMeta | None:
    """从 .docx 文件提取元数据，非docx格式返回 None"""
    if not file_path.lower().endswith(".docx"):
        logger.debug(f"非 .docx 文件，跳过元数据提取: {file_path}")
        return None
    try:
        import docx  # python-docx
        doc = docx.Document(file_path)
        props = doc.core_properties
        meta = DocxMeta(
            author=props.author or "",
            last_modified_by=props.last_modified_by or "",
            company=props.category or "",  # category 有时存company
            created=props.created,
            modified=props.modified,
            revision=props.revision or 0,
            source_path=file_path,
        )
        logger.debug(
            f"元数据提取: author={meta.author!r}, modified_by={meta.last_modified_by!r}, "
            f"created={meta.created}, modified={meta.modified}"
        )
        return meta
    except Exception as e:
        logger.warning(f"元数据提取失败 ({file_path}): {e}")
        return None


def _to_utc(dt: datetime | None) -> datetime | None:
    """确保 datetime 有时区信息（naive → UTC）"""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def compare_meta(meta_a: DocxMeta | None, meta_b: DocxMeta | None) -> MetaComparison:
    """对比两份文档的元数据，返回风险分析结果"""
    result = MetaComparison()

    if meta_a is None or meta_b is None:
        logger.info("至少一份文档无法提取元数据，跳过元数据对比")
        return result

    notes: list[str] = []

    # 作者对比（非空时才对比）
    if meta_a.author and meta_b.author and meta_a.author == meta_b.author:
        result.same_author = True
        notes.append(f"两份文档作者相同：{meta_a.author!r}")

    # 最后修改人对比
    if (
        meta_a.last_modified_by
        and meta_b.last_modified_by
        and meta_a.last_modified_by == meta_b.last_modified_by
    ):
        result.same_last_modifier = True
        notes.append(f"两份文档最后修改人相同：{meta_a.last_modified_by!r}")

    # 公司对比
    if meta_a.company and meta_b.company and meta_a.company == meta_b.company:
        result.same_company = True
        notes.append(f"两份文档公司属性相同：{meta_a.company!r}")

    # 修改时间差
    mod_a = _to_utc(meta_a.modified)
    mod_b = _to_utc(meta_b.modified)
    if mod_a is not None and mod_b is not None:
        gap_minutes = abs((mod_a - mod_b).total_seconds()) / 60.0
        result.time_gap_minutes = gap_minutes
        if gap_minutes <= 30:
            result.is_timestamp_clustered = True
            notes.append(
                f"两份文档修改时间相差 {gap_minutes:.1f} 分钟（≤30分钟），疑似同批次制作"
            )

    result.risk_notes = notes

    # 风险等级判定
    if result.same_author or result.same_company:
        result.risk_level = "high"
    elif result.is_timestamp_clustered or result.same_last_modifier:
        result.risk_level = "medium"
    else:
        result.risk_level = "none"

    logger.info(f"元数据对比: {notes}, risk={result.risk_level}")
    return result

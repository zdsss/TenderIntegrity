"""analyze_structure_and_fields 节点：文档结构相似度 + 关键字段重叠检测 + Q1/Q2/Q3 分析"""
import logging
from dataclasses import asdict

from src.analysis.structure_comparator import StructureComparator
from src.analysis.field_overlap_detector import FieldOverlapDetector
from src.analysis.rare_token_analyzer import RareTokenAnalyzer
from src.analysis.price_analyzer import PriceAnalyzer
from src.document.field_extractor import KeyFieldExtractor
from src.document.docx_meta import extract_docx_meta, compare_meta
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def analyze_structure_and_fields(state: TenderComparisonState) -> dict:
    chunks = state.get("chunks", {})
    doc_ids = state.get("doc_ids", [])
    file_paths = state.get("file_paths", {})

    if len(doc_ids) < 2:
        logger.warning("少于两份文档，跳过结构/字段分析")
        return {
            "structure_similarity": None,
            "field_overlaps": [],
            "rare_token_analysis": None,
            "price_analysis": None,
            "meta_comparison": None,
            "current_node": "analyze_structure_and_fields",
            "processing_progress": 0.25,
        }

    doc_id_a, doc_id_b = doc_ids[0], doc_ids[1]
    chunks_a = chunks.get(doc_id_a, [])
    chunks_b = chunks.get(doc_id_b, [])

    # ── 结构相似度 ────────────────────────────────────────────────────────
    comparator = StructureComparator()
    structure = comparator.compare(chunks_a, chunks_b)

    # ── 关键字段提取与重叠检测 ────────────────────────────────────────────
    extractor = KeyFieldExtractor()
    fields_a = extractor.extract(chunks_a)
    fields_b = extractor.extract(chunks_b)
    detector = FieldOverlapDetector()
    overlaps = detector.detect(fields_a, fields_b)

    # ── Q1：罕见序列分析 ──────────────────────────────────────────────────
    rare_analyzer = RareTokenAnalyzer()
    rare_result = rare_analyzer.analyze(chunks_a, chunks_b)
    rare_dict = {
        "risk_level": rare_result.risk_level,
        "total_match_count": rare_result.total_match_count,
        "number_unit_matches": rare_result.number_unit_matches,
        "matches": [
            {
                "token": m.token,
                "freq_in_a": m.freq_in_a,
                "freq_in_b": m.freq_in_b,
                "token_type": m.token_type,
                "risk_note": m.risk_note,
            }
            for m in rare_result.matches
        ],
    }

    # ── Q2：价格异常分析 ──────────────────────────────────────────────────
    price_analyzer = PriceAnalyzer()
    price_result = price_analyzer.analyze(chunks_a, chunks_b)
    price_dict = {
        "risk_level": price_result.risk_level,
        "total_a": price_result.total_a,
        "total_b": price_result.total_b,
        "proximity_ratio": price_result.proximity_ratio,
        "is_price_coordinated": price_result.is_price_coordinated,
        "coordinated_evidence": price_result.coordinated_evidence,
    }

    # ── Q3：DOCX 元数据对比 ────────────────────────────────────────────────
    path_a = file_paths.get(doc_id_a, "")
    path_b = file_paths.get(doc_id_b, "")
    meta_a = extract_docx_meta(path_a)
    meta_b = extract_docx_meta(path_b)
    meta_result = compare_meta(meta_a, meta_b)
    meta_dict = {
        "risk_level": meta_result.risk_level,
        "same_author": meta_result.same_author,
        "same_last_modifier": meta_result.same_last_modifier,
        "same_company": meta_result.same_company,
        "time_gap_minutes": meta_result.time_gap_minutes,
        "is_timestamp_clustered": meta_result.is_timestamp_clustered,
        "risk_notes": meta_result.risk_notes,
    }

    logger.info(
        f"结构分析完成: score={structure.overall_score}, risk={structure.structure_risk_level}; "
        f"字段重叠: {len(overlaps)} 项; 罕见序列: {rare_result.total_match_count} 项; "
        f"价格风险: {price_result.risk_level}; 元数据风险: {meta_result.risk_level}"
    )

    structure_dict = {
        "title_jaccard": structure.title_jaccard,
        "sequence_similarity": structure.sequence_similarity,
        "matched_sections": structure.matched_sections,
        "structure_risk_level": structure.structure_risk_level,
        "overall_score": structure.overall_score,
    }

    overlaps_list = [
        {
            "field_type": o.field_type,
            "value_a": o.value_a,
            "value_b": o.value_b,
            "overlap_type": o.overlap_type,
            "risk_note": o.risk_note,
        }
        for o in overlaps
    ]

    return {
        "structure_similarity": structure_dict,
        "field_overlaps": overlaps_list,
        "rare_token_analysis": rare_dict,
        "price_analysis": price_dict,
        "meta_comparison": meta_dict,
        "current_node": "analyze_structure_and_fields",
        "processing_progress": 0.25,
    }

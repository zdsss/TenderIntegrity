"""analyze_structure_and_fields 节点：文档结构相似度 + 关键字段重叠检测"""
import logging
from src.analysis.structure_comparator import StructureComparator
from src.analysis.field_overlap_detector import FieldOverlapDetector
from src.document.field_extractor import KeyFieldExtractor
from src.workflow.state import TenderComparisonState

logger = logging.getLogger(__name__)


def analyze_structure_and_fields(state: TenderComparisonState) -> dict:
    chunks = state.get("chunks", {})
    doc_ids = state.get("doc_ids", [])

    if len(doc_ids) < 2:
        logger.warning("少于两份文档，跳过结构/字段分析")
        return {
            "structure_similarity": None,
            "field_overlaps": [],
            "current_node": "analyze_structure_and_fields",
            "processing_progress": 0.25,
        }

    doc_id_a, doc_id_b = doc_ids[0], doc_ids[1]
    chunks_a = chunks.get(doc_id_a, [])
    chunks_b = chunks.get(doc_id_b, [])

    # 结构相似度
    comparator = StructureComparator()
    structure = comparator.compare(chunks_a, chunks_b)

    # 关键字段提取与重叠检测
    extractor = KeyFieldExtractor()
    fields_a = extractor.extract(chunks_a)
    fields_b = extractor.extract(chunks_b)
    detector = FieldOverlapDetector()
    overlaps = detector.detect(fields_a, fields_b)

    logger.info(
        f"结构分析完成: score={structure.overall_score}, risk={structure.structure_risk_level}; "
        f"字段重叠: {len(overlaps)} 项"
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
        "current_node": "analyze_structure_and_fields",
        "processing_progress": 0.25,
    }

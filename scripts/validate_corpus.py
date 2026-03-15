"""测试语料验证脚本

运行三组测试语料（Group1/2/3）并输出检测覆盖率矩阵。

用法：
    uv run python scripts/validate_corpus.py [--corpus-dir PATH]

若未提供语料目录，默认读取 tests/corpus/ 目录下的文件。
语料目录预期结构：
    corpus/
        group1/
            C1.docx (或 .txt)
            C2.docx
            C3.docx
        group2/
            P1.docx
            ...
        group3/
            M1.docx
            ...
"""
import argparse
import sys
import os
import logging
from pathlib import Path

# 确保项目根路径在 sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

from src.document.parser import parse_document
from src.document.chunker import ChunkSplitter
from src.analysis.structure_comparator import StructureComparator
from src.analysis.field_overlap_detector import FieldOverlapDetector
from src.document.field_extractor import KeyFieldExtractor
from src.analysis.rare_token_analyzer import RareTokenAnalyzer
from src.analysis.price_analyzer import PriceAnalyzer
from src.document.docx_meta import extract_docx_meta, compare_meta
from src.analysis.risk_synthesizer import RiskSynthesizer


def load_doc(path: Path):
    """解析文档，返回 chunks 列表"""
    raw_text = parse_document(str(path))
    splitter = ChunkSplitter()
    doc_id = path.stem
    chunks = splitter.split(raw_text, doc_id=doc_id)
    return chunks


def analyze_pair(path_a: Path, path_b: Path) -> dict:
    """对两份文档执行 Phase 3 全维度分析，返回综合风险结果"""
    chunks_a = load_doc(path_a)
    chunks_b = load_doc(path_b)

    # 结构分析
    comparator = StructureComparator()
    structure = comparator.compare(chunks_a, chunks_b)
    structure_dict = {
        "overall_score": structure.overall_score,
        "structure_risk_level": structure.structure_risk_level,
    }

    # 字段重叠
    extractor = KeyFieldExtractor()
    fields_a = extractor.extract(chunks_a)
    fields_b = extractor.extract(chunks_b)
    detector = FieldOverlapDetector()
    overlaps = detector.detect(fields_a, fields_b)
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

    # 罕见序列
    rare_analyzer = RareTokenAnalyzer()
    rare_result = rare_analyzer.analyze(chunks_a, chunks_b)
    rare_dict = {
        "risk_level": rare_result.risk_level,
        "total_match_count": rare_result.total_match_count,
    }

    # 价格分析
    price_analyzer = PriceAnalyzer()
    price_result = price_analyzer.analyze(chunks_a, chunks_b)
    price_dict = {
        "risk_level": price_result.risk_level,
        "proximity_ratio": price_result.proximity_ratio,
    }

    # 元数据对比
    meta_a = extract_docx_meta(str(path_a))
    meta_b = extract_docx_meta(str(path_b))
    meta_result = compare_meta(meta_a, meta_b)
    meta_dict = {
        "risk_level": meta_result.risk_level,
        "is_timestamp_clustered": meta_result.is_timestamp_clustered,
        "risk_notes": meta_result.risk_notes,
    }

    # 综合合成（文本维度使用简化评估）
    # 注：完整流程需向量检索+LLM，此处用结构分作为文本风险代理
    text_rate = structure.overall_score / 100.0 * 0.5  # 简化代理
    if structure.structure_risk_level == "high":
        text_level = "high"
    elif structure.structure_risk_level == "medium":
        text_level = "medium"
    else:
        text_level = "low"

    synthesizer = RiskSynthesizer()
    composite = synthesizer.synthesize(
        text_level=text_level,
        text_rate=text_rate,
        structure=structure_dict,
        field_overlaps=overlaps_list,
        rare_token=rare_dict,
        price=price_dict,
        meta=meta_dict,
    )

    return {
        "pair": f"{path_a.stem} vs {path_b.stem}",
        "structure_score": structure.overall_score,
        "structure_risk": structure.structure_risk_level,
        "field_overlap_count": len(overlaps_list),
        "rare_token_count": rare_result.total_match_count,
        "price_risk": price_result.risk_level,
        "meta_risk": meta_result.risk_level,
        "composite_level": composite.final_level,
        "triggered_signals": composite.triggered_signals,
    }


def print_matrix(results: list[dict], expected_map: dict[str, str]):
    """输出覆盖率矩阵"""
    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"

    header = f"{'语料对':<25} {'期望风险':<10} {'系统判定':<10} {'命中':<6} {'触发信号数'}"
    print("\n" + "=" * 70)
    print("TenderIntegrity Phase 3 — 语料覆盖率矩阵")
    print("=" * 70)
    print(header)
    print("-" * 70)

    hits = 0
    for r in results:
        pair = r["pair"]
        expected = expected_map.get(pair, "unknown")
        actual = r["composite_level"]
        hit = expected == actual
        if hit:
            hits += 1

        color = GREEN if hit else RED
        hit_str = f"{color}{'✓' if hit else '✗'}{RESET}"
        signal_count = len(r["triggered_signals"])
        print(f"{pair:<25} {expected:<10} {actual:<10} {hit_str:<6}  {signal_count}")

        if r["triggered_signals"]:
            for sig in r["triggered_signals"][:2]:
                print(f"  {'':25}  → {sig[:60]}")

    print("-" * 70)
    print(f"命中率: {hits}/{len(results)} ({hits/len(results)*100:.0f}%)\n")


def discover_corpus(corpus_dir: Path) -> list[tuple[Path, Path, str, str]]:
    """
    发现语料文件对，返回 (path_a, path_b, pair_key, expected_risk) 列表。
    规则：
    - group1/: C1 vs C2, C1 vs C3, C2 vs C3 → 期望 low
    - group2/: 任意两两对比 → 期望 high（若包含 P5 则为 high）
    - group3/: 任意两两对比 → 期望 high
    """
    pairs = []
    for group_dir in sorted(corpus_dir.iterdir()):
        if not group_dir.is_dir():
            continue
        group = group_dir.name.lower()
        docs = sorted([
            f for f in group_dir.iterdir()
            if f.suffix in (".docx", ".txt", ".pdf") and not f.name.startswith(".")
        ])
        if len(docs) < 2:
            continue

        if "group1" in group or "g1" in group:
            expected = "low"
        else:
            expected = "high"

        for i in range(len(docs)):
            for j in range(i + 1, len(docs)):
                pair_key = f"{docs[i].stem} vs {docs[j].stem}"
                pairs.append((docs[i], docs[j], pair_key, expected))

    return pairs


def main():
    parser = argparse.ArgumentParser(description="TenderIntegrity Phase 3 语料验证脚本")
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=ROOT / "tests" / "corpus",
        help="测试语料目录（默认 tests/corpus/）",
    )
    args = parser.parse_args()

    corpus_dir: Path = args.corpus_dir
    if not corpus_dir.exists():
        print(f"[警告] 语料目录不存在: {corpus_dir}")
        print("请创建 tests/corpus/group1/, tests/corpus/group2/, tests/corpus/group3/ 并放入文档。")
        print("\n示例输出（无实际语料时）：")
        _demo_output()
        return

    pairs = discover_corpus(corpus_dir)
    if not pairs:
        print(f"[警告] 语料目录 {corpus_dir} 中未发现有效文件对（需 .docx/.txt/.pdf）")
        return

    print(f"发现 {len(pairs)} 对文档，开始分析...\n")
    results = []
    expected_map = {}
    for path_a, path_b, pair_key, expected in pairs:
        print(f"  分析: {pair_key} ...", end="", flush=True)
        try:
            result = analyze_pair(path_a, path_b)
            results.append(result)
            expected_map[pair_key] = expected
            print(f" → {result['composite_level']}")
        except Exception as e:
            print(f" [错误] {e}")

    print_matrix(results, expected_map)


def _demo_output():
    """展示期望输出格式（无实际语料时）"""
    demo = [
        {"pair": "C1 vs C2", "composite_level": "?", "triggered_signals": []},
        {"pair": "C1 vs C3", "composite_level": "?", "triggered_signals": []},
        {"pair": "C2 vs C3", "composite_level": "?", "triggered_signals": []},
        {"pair": "P1 vs C1", "composite_level": "?", "triggered_signals": []},
        {"pair": "M1 vs M2", "composite_level": "?", "triggered_signals": []},
    ]
    expected = {
        "C1 vs C2": "low", "C1 vs C3": "low", "C2 vs C3": "low",
        "P1 vs C1": "high", "M1 vs M2": "high",
    }
    header = f"{'语料对':<25} {'期望风险':<10} {'系统判定':<10} {'命中':<6}"
    print(header)
    print("-" * 55)
    for r in demo:
        pair = r["pair"]
        exp = expected.get(pair, "?")
        print(f"{pair:<25} {exp:<10} {'?':<10} {'?':<6}")


if __name__ == "__main__":
    main()

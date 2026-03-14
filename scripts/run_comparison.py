#!/usr/bin/env python3
"""CLI 入口：触发标书比对任务（不依赖 API 服务器）"""
import argparse
import json
import logging
import sys
import uuid
from pathlib import Path

# 确保项目根目录在 Python 路径中
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="TenderIntegrity — 标书雷同与语义查重",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/run_comparison.py \\
    --doc-a doc/测试样本A_疑似围标投标文件.docx \\
    --doc-b doc/测试样本B_疑似围标投标文件.docx \\
    --output reports/

  python scripts/run_comparison.py \\
    --docs doc/A.docx doc/B.docx doc/C.docx \\
    --mode all_vs_all \\
    --output reports/
        """,
    )
    parser.add_argument("--doc-a", type=str, help="文档A路径（两文档比对模式）")
    parser.add_argument("--doc-b", type=str, help="文档B路径（两文档比对模式）")
    parser.add_argument("--docs", nargs="+", type=str, help="多文档路径（3+文档）")
    parser.add_argument(
        "--mode",
        choices=["pairwise", "all_vs_all"],
        default="pairwise",
        help="比对模式 (默认: pairwise)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./reports",
        help="报告输出目录 (默认: ./reports)",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="跳过 LLM 分析（仅向量检索+评分）",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # 收集文档路径
    if args.docs:
        file_paths_list = args.docs
    elif args.doc_a and args.doc_b:
        file_paths_list = [args.doc_a, args.doc_b]
    else:
        print("错误: 请提供至少两份文档（--doc-a/--doc-b 或 --docs）")
        sys.exit(1)

    # 验证文件存在
    for fp in file_paths_list:
        if not Path(fp).exists():
            print(f"错误: 文件不存在: {fp}")
            sys.exit(1)

    # 构建 doc_id -> file_path 映射
    doc_ids = [f"doc_{i:02d}" for i in range(len(file_paths_list))]
    file_paths = dict(zip(doc_ids, file_paths_list))
    doc_names = {
        doc_id: Path(fp).name
        for doc_id, fp in file_paths.items()
    }

    task_id = str(uuid.uuid4())[:8]
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print("TenderIntegrity — 标书雷同与语义查重")
    print(f"{'='*60}")
    print(f"任务 ID: {task_id}")
    print(f"比对模式: {args.mode}")
    print("文档列表:")
    for doc_id, fp in file_paths.items():
        print(f"  {doc_id}: {fp}")
    print(f"{'='*60}\n")

    # 构建初始状态
    from src.workflow.state import TenderComparisonState
    from src.workflow.graph import compile_graph

    initial_state: TenderComparisonState = {
        "task_id": task_id,
        "doc_ids": doc_ids,
        "file_paths": file_paths,
        "doc_names": doc_names,
        "comparison_mode": args.mode,
        "raw_texts": {},
        "chunks": {},
        "embeddings_stored": False,
        "candidate_pairs": [],
        "scored_pairs": [],
        "llm_analyzed_pairs": [],
        "current_node": "start",
        "error_message": None,
        "processing_progress": 0.0,
        "report": None,
        "overall_risk_level": "low",
        "overall_similarity_rate": 0.0,
    }

    if args.skip_llm:
        # 修改图：跳过 LLM 节点
        from src.workflow.nodes.score_node import score_candidates
        from src.workflow.nodes.report_node import generate_report
        from src.workflow.nodes.parse_node import parse_documents
        from src.workflow.nodes.chunk_node import chunk_documents
        from src.workflow.nodes.whitelist_node import filter_whitelist
        from src.workflow.nodes.embed_node import embed_and_store
        from src.workflow.nodes.retrieve_node import retrieve_similar_pairs
        from src.workflow.nodes.error_node import handle_error
        from langgraph.graph import StateGraph, START, END

        graph = StateGraph(TenderComparisonState)
        graph.add_node("parse_documents", parse_documents)
        graph.add_node("chunk_documents", chunk_documents)
        graph.add_node("filter_whitelist", filter_whitelist)
        graph.add_node("embed_and_store", embed_and_store)
        graph.add_node("retrieve_similar_pairs", retrieve_similar_pairs)
        graph.add_node("score_candidates", score_candidates)
        graph.add_node("generate_report", generate_report)
        graph.add_node("handle_error", handle_error)
        graph.add_edge(START, "parse_documents")
        graph.add_conditional_edges(
            "parse_documents",
            lambda s: "handle_error" if s.get("error_message") else "chunk_documents",
        )
        graph.add_edge("chunk_documents", "filter_whitelist")
        graph.add_edge("filter_whitelist", "embed_and_store")
        graph.add_edge("embed_and_store", "retrieve_similar_pairs")
        graph.add_edge("retrieve_similar_pairs", "score_candidates")
        graph.add_edge("score_candidates", "generate_report")
        graph.add_edge("generate_report", END)
        graph.add_edge("handle_error", END)
        app = graph.compile()
    else:
        app = compile_graph()

    print("开始处理...\n")
    final_state = app.invoke(initial_state)

    # 检查错误
    if final_state.get("error_message"):
        print(f"\n❌ 处理失败: {final_state['error_message']}")
        sys.exit(1)

    report = final_state.get("report", {})
    if not report:
        print("\n⚠️ 未生成报告")
        sys.exit(1)

    # 导出报告
    from src.report.generator import ReportGenerator
    generator = ReportGenerator(output_dir)
    paths = generator.export_all(report, task_id)

    # 打印摘要
    overall_risk = report.get("overall_risk_level", "unknown")
    similarity_rate = report.get("overall_similarity_rate", 0)
    summary = report.get("risk_summary", {})

    risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(overall_risk, "⚪")

    print(f"\n{'='*60}")
    print("分析完成！")
    print(f"{'='*60}")
    print(f"{risk_emoji} 整体风险等级: {overall_risk.upper()}")
    print(f"📊 整体雷同率: {similarity_rate:.1%}")
    print(f"🔴 高风险段落对: {summary.get('high_count', 0)}")
    print(f"🟡 中风险段落对: {summary.get('medium_count', 0)}")
    print(f"🟢 低风险段落对: {summary.get('low_count', 0)}")
    print(f"\n报告文件:")
    for fmt, path in paths.items():
        print(f"  {fmt.upper()}: {path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
